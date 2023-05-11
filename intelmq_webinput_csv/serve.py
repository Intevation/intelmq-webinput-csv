#!/usr/bin/env python3
"""Provides an API for IntelMQ

Requires hug (http://www.hug.rest/)

Development: call like
  hug -f serve.py
  connect to http://localhost:8000/

Several configuration methods are shown within the code.


SPDX-FileCopyrightText: 2016, 2017, 2022-2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later

Software engineering by Intevation GmbH

This program is Free Software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Author(s):
    * Raimund Renkert <raimund.renkert@intevation.de>
    * Sebastian Wagner <swagner@intevation.de>
"""

import io
import json
import logging
import os
import sys
import traceback
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from typing import Optional
from pkg_resources import resource_filename

import dateutil.parser
import falcon
import hug
from intelmq import CONFIG_DIR, HARMONIZATION_CONF_FILE
from intelmq.bots.experts.taxonomy.expert import TAXONOMY
try:
    from intelmq.lib.bot import BotLibSettings, Bot
except ImportError:
    BotLibSettings = None
    Bot = None
from intelmq.lib.exceptions import InvalidValue, IntelMQException
from intelmq.lib.harmonization import DateTime
from intelmq.lib.message import Event, MessageFactory
from intelmq.lib.pipeline import PipelineFactory
from intelmq.lib.utils import load_configuration
from intelmq.lib.datatypes import BotType, Dict39

from webinput_session import config, session
from intelmq_webinput_csv.sql_output import WebinputSQLOutputBot

try:
    from intelmqmail import cb
    from intelmqmail.db import open_db_connection
except ImportError:
    cb = None
else:
    # only needed if intelmqmail is available
    from psycopg2.extras import RealDictConnection

try:
    EVENT_FIELDS = load_configuration(HARMONIZATION_CONF_FILE)
except ValueError:
    # Fallback to internal harmonization file
    EVENT_FIELDS = load_configuration(resource_filename('intelmq', 'etc/harmonization.conf'))

# Logging
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)  # using INFO as default, otherwise it's WARNING

log.debug("prepare session config")
session_config: config.Config = config.Config(os.environ.get("WEBINPUT_CSV_SESSION_CONFIG"))

ENDPOINTS = {}
ENDPOINT_PREFIX = '/webinput'

# Read parameters from config
CONFIG_FILE = os.path.join(CONFIG_DIR, 'webinput_csv.conf')
ENV_CONFIG_FILE = os.environ.get("WEBINPUT_CSV_CONFIG")
config = False

configfiles = [
    Path(CONFIG_FILE),
    Path('/etc/intelmq/webinput_csv.conf')
]
if ENV_CONFIG_FILE:
    configfiles.insert(0, Path(ENV_CONFIG_FILE).resolve())

for path in configfiles:
    if path and path.exists() and path.is_file():
        print(f"Loading config from {path}")
        config = True
        with path.open() as f:
            CONFIG = json.load(f)
            ENDPOINT_PREFIX = CONFIG.get('prefix', '/webinput')
            if ENDPOINT_PREFIX.endswith('/'):
                ENDPOINT_PREFIX = ENDPOINT_PREFIX[:-1]
            CONSTANTS = CONFIG.get('constant_fields', '{}')


@hug.startup()
def setup(api):
    session.initialize_sessions(session_config)
    pass


@hug.post(ENDPOINT_PREFIX + '/api/login')
def login(username: str, password: str):
    if session.session_store is not None:
        known = session.session_store.verify_user(username, password)
        if known is not None:
            token = session.session_store.new_session({"username": username})
            return {"login_token": token,
                    "username": username,
                    }
        else:
            return "Invalid username and/or password"
    else:
        return {"login_token": "none",
                "username": "none"
                }


def row_to_event(item: dict, body: dict,
                 retval: Optional[defaultdict] = None,
                 lineno: int = 0, time_observation: Optional[str] = None) -> Event:
    """
    Processes a row of the data
    """
    if not time_observation:
        time_observation = DateTime().generate_datetime_now()
    if retval is None:
        # is not used then, but to keep the code below cleaner
        retval = defaultdict(list)

    event = Event()
    line_valid = True
    for key in item:
        value = item[key]
        if key.startswith('time.'):
            try:
                parsed = dateutil.parser.parse(value, fuzzy=True)
                if not parsed.tzinfo:
                    value += body['timezone']
                    parsed = dateutil.parser.parse(value)
                value = parsed.isoformat()
            except ValueError:
                line_valid = False
        try:
            event.add(key, value)
        except IntelMQException as exc:
            retval[lineno].append(f"Failed to add data {value!r} as field {key!r}: {exc!s}")
            line_valid = False
    for key in CONSTANTS:
        if key not in event:
            try:
                event.add(key, CONSTANTS[key])
            except InvalidValue as exc:
                retval[lineno].append(f"Failed to add data {CONSTANTS[key]!r} as field {key!r}: {exc!s}")
                line_valid = False
    for key in body['custom']:
        if not key.startswith('custom_'):
            continue
        if key[7:] not in event:
            try:
                event.add(key[7:], body['custom'][key])
            except InvalidValue as exc:
                retval[lineno].append(f"Failed to add data {body['custom'][key]!r} as field {key!r}: {exc!s}")
                line_valid = False

    if 'classification.type' not in event:
        event.add('classification.type', 'test')
    if 'classification.identifier' not in event:
        event.add('classification.identifier', 'test')
    if 'feed.code' not in event:
        event.add('feed.code', 'oneshot')
    if 'time.observation' not in event:
        event.add('time.observation', time_observation, sanitize=False)

    # Ensure dryrun has priority, overwrite it at the end
    if body['dryrun']:
        event.add('classification.identifier', 'test', overwrite=True)
        event.add('classification.type', 'test', overwrite=True)

    return event, line_valid


@hug.post(ENDPOINT_PREFIX + '/api/upload', requires=session.token_authentication)
def uploadCSV(body, request, response):
    # additional authentication is required for this call
    if body.get('submit', True) and session.session_store is not None:
        username = body.get('username')
        password = body.get('password')
        known = session.session_store.verify_user(username, password)
        if known is None:
            response.status = falcon.HTTP_401
            return "Invalid username and/or password"

    destination_pipeline = PipelineFactory.create(pipeline_args=CONFIG['intelmq'],
                                                  logger=log,
                                                  direction='destination')
    if not CONFIG.get('destination_pipeline_queue_formatted', False):
        destination_pipeline.set_queues(CONFIG['destination_pipeline_queue'], "destination")
        destination_pipeline.connect()
    time_observation = DateTime().generate_datetime_now()
    required_fields = CONFIG.get('required_fields')

    data = body["data"]
    if 'custom' not in body:
        body["custom"] = {}
    retval = defaultdict(list)
    lines_valid = 0

    if cb:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        conn = open_db_connection(mailgen_config, connection_factory=RealDictConnection)

    bots = []
    for bot_id, bot_config in CONFIG.get('bots', {}).items() if body.get('validate_with_bots', False) else {}:
        log.info('init bot %s', bot_id)
        try:
            bot = import_module(bot_config['module']).BOT
            kwargs = {}
            if bot is WebinputSQLOutputBot:
                kwargs = {'connection': conn}
            bots.append((bot_id, bot(bot_id, **kwargs, settings=BotLibSettings | bot_config.get('parameters', {}))))
        except Exception:
            return {'status': 'error',
                    'log': traceback.format_exc()}

    for lineno, item in enumerate(data):
        if not item:
            retval[lineno] = ('Line is empty', )
            continue

        event, line_valid = row_to_event(item, body, retval, lineno, time_observation)

        bots_input = [event]
        for bot_id, bot in bots:
            bots_output = []
            # log.info('messages before bot processing: %r', bots_input)
            try:
                queues = bot.process_message(*bots_input)
            except Exception:
                return {'status': 'error',
                        'log': traceback.format_exc()}
            bots_output.extend(queues['output'])
            # log.info(f'messages after processing by {bot}: %r', queues['output'])
            bots_input = bots_output
        if not bots:
            bots_output = [event]

        for event in bots_output:
            try:
                if CONFIG.get('destination_pipeline_queue_formatted', False):
                    CONFIG['destination_pipeline_queue'].format(ev=event)
            except Exception as exc:
                retval[lineno].append(f"Failed to generate destination_pipeline_queue {CONFIG['destination_pipeline_queue']}: {exc!s}")
                line_valid = False
            if not line_valid:
                continue

            if required_fields:
                diff = set(required_fields) - event.keys()
                if diff:
                    line_valid = False
                    retval[lineno].append(f"Line is missing these required fields: {', '.join(diff)}")

            # if 'raw' not in event:
            #     event.add('raw', ''.join(raw_header + [handle_rewindable.current_line]))
            raw_message = MessageFactory.serialize(event)
            if body.get('submit', True) and line_valid:
                destination_pipeline.send(raw_message)
        # if line was valid, increment the counter by 1
        lines_valid += line_valid

    if body['dryrun'] and cb:
        conn.rollback()
    elif cb:
        conn.commit()

    # lineno is the index, for the number of lines add one
    total_lines = lineno + 1 if data else 0
    result = {"total": total_lines,
              "lines_invalid": total_lines - lines_valid,
              "errors": retval}
    return result


@hug.get(ENDPOINT_PREFIX + '/api/classification/types', requires=session.token_authentication)
def classification_types():
    return TAXONOMY


@hug.get(ENDPOINT_PREFIX + '/api/harmonization/event/fields', requires=session.token_authentication)
def harmonization_event_fields():
    return EVENT_FIELDS['event']


@hug.get(ENDPOINT_PREFIX + '/api/custom/fields', requires=session.token_authentication)
def custom_fields():
    return CONFIG.get('custom_input_fields', {})


@hug.get(ENDPOINT_PREFIX + '/api/custom/required_fields', requires=session.token_authentication)
def get_required_fields():
    return CONFIG.get('required_fields', [])


@hug.get(ENDPOINT_PREFIX + '/api/mailgen/target_groups', requires=session.token_authentication)
def get_mailgen_target_groups():
    """
    Return configured mailgen target groups
    Actually the target group is used by a rules expert's rule.
    """
    return CONFIG.get('mailgen_target_groups', [])


#  TODO for now show the full api documentation that hug generates
# @hug.get("/")
# def get_endpoints():
#     return ENDPOINTS


@hug.get(ENDPOINT_PREFIX + '/api/mailgen/available', requires=session.token_authentication)
def mailgen_available():
    """
    Returns true/false if mailgen is installed on the system.
    """
    return bool(cb)


@hug.post(ENDPOINT_PREFIX + '/api/mailgen/run', requires=session.token_authentication)
def mailgen_run(body, request, response):
    """
    Start mailgen
    """
    template = body.get('template')

    log = io.StringIO()
    log_handler = logging.StreamHandler(stream=log)
    logging.getLogger('intelmqmail').addHandler(log_handler)

    if body.get('verbose'):
        logging.getLogger('intelmqmail').setLevel(logging.DEBUG)
    else:
        logging.getLogger('intelmqmail').setLevel(logging.INFO)

    if cb is None:
        response.status = falcon.status.HTTP_500
        return {"result": "intelmqmail is not available on this system."}

    try:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        return {"result": cb.start(mailgen_config, process_all=True, template=template, dry_run=body.get('dry_run')),
                "log": log.getvalue().strip()}
    except Exception:
        response.status = falcon.status.HTTP_500
        traceback.print_exc(file=sys.stderr)
        return {"result": str(traceback.format_exc()), "log": log.getvalue()}


@hug.post(ENDPOINT_PREFIX + '/api/mailgen/preview', requires=session.token_authentication)
def mailgen_preview(body, request, response):
    """
    Show mailgen email preview
    """
    template = body.get('template')

    mailgen_log = io.StringIO()
    log_handler = logging.StreamHandler(stream=mailgen_log)
    logging.getLogger('intelmqmail').addHandler(log_handler)

    if body.get('verbose'):
        logging.getLogger('intelmqmail').setLevel(logging.DEBUG)
    else:
        logging.getLogger('intelmqmail').setLevel(logging.INFO)

    if cb is None:
        response.status = falcon.status.HTTP_500
        return {"result": "intelmqmail is not available on this system."}

    try:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        conn = open_db_connection(mailgen_config, connection_factory=RealDictConnection)
        return {"result": cb.start(mailgen_config, process_all=True, template=template, get_preview=True,
                                   conn=conn)[0],  # only transmit the first notification
                "log": mailgen_log.getvalue().strip()}
    except Exception:
        response.status = falcon.status.HTTP_500
        traceback.print_exc(file=sys.stderr)
        return {"result": str(traceback.format_exc()), "log": mailgen_log.getvalue()}


@hug.get(ENDPOINT_PREFIX + '/api/bots/available', requires=session.token_authentication)
def bots_available() -> dict:
    """
    Checks if bots are available: IntelMQ Core version supports the feature and at least one bot is configured.
    """
    config_has_bots = bool(CONFIG.get('bots'))
    intelmq_supports_bot_lib = BotLibSettings and Bot and hasattr(Bot, 'process_message')
    return {
        "status": config_has_bots and intelmq_supports_bot_lib,
        "reason": "IntelMQ does not support calling Bots as library (IntelMQ >= 3.2.0)" if not intelmq_supports_bot_lib else ("No bots configured." if not config_has_bots else f"Bots: {','.join(CONFIG.get('bots'))}")
    }


@hug.post(ENDPOINT_PREFIX + '/api/bots/process', requires=session.token_authentication)
def process(body) -> dict:
    """
    Process data with IntelMQ bots
    """
    data = body.get('data', [])
    if not data:
        return {'status': 'error',
                'log': 'No data supplied. Did you set fields for the columns?'}

    bot_logs = io.StringIO()
    log_handler = logging.StreamHandler(stream=bot_logs)

    if cb:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        conn = open_db_connection(mailgen_config, connection_factory=RealDictConnection)

    bots = []
    for bot_id, bot_config in CONFIG.get('bots', {}).items():
        try:
            logging.getLogger(bot_id).addHandler(log_handler)
            bot = import_module(bot_config['module']).BOT
            kwargs = {}
            if bot is WebinputSQLOutputBot:
                kwargs = {'connection': conn}
            bots.append((bot_id, bot(bot_id, **kwargs, settings=BotLibSettings | Dict39({'logging_level': 'DEBUG'}) | Dict39(bot_config.get('parameters', {})))))
        except Exception:
            return {'status': 'error',
                    'log': traceback.format_exc()}
    bots_input = []
    for item in data:
        if not item:
            return {'status': 'error',
                    'log': 'No data supplied for at least one row. Did you set fields for the columns?'}
        # log.info('message before converting: %r', item)
        retval = {0: []}
        first_message, line_valid = row_to_event(item, body, retval)
        if not line_valid:
            return {'status': 'error',
                    'log': f"Line was not valid: {'.'.join(retval[0])}"}
        bots_input.append(first_message)

    for bot_id, bot in bots:
        # log.info('messages before bot processing: %r', bots_input)
        try:
            queues = bot.process_message(*bots_input)
        except Exception:
            return {'status': 'error',
                    'log': traceback.format_exc()}
        # for output bots, the output quue is empty, don't consider it
        if bot.bottype is not BotType.OUTPUT:
            bots_output = queues['output']
        # log.info(f'messages after processing by {bot}: %r', queues['output'])
        bots_input = bots_output

    retval = {'status': 'success',
              'messages': bots_output,
              'log': bot_logs.getvalue()}

    if cb:
        mailgen_log = io.StringIO()
        log_handler = logging.StreamHandler(stream=mailgen_log)
        logging.getLogger('intelmqmail').addHandler(log_handler)
        logging.getLogger('intelmqmail').setLevel(logging.DEBUG)

        retval['log'] += mailgen_log.getvalue().strip()
        retval['notifications'] = cb.start(mailgen_config, process_all=True,
                                           template=body.get('template'),
                                           get_preview=True,
                                           conn=conn,
                                           dry_run=True)

        # in dry_run, mailgen calls conn.rollback() itself

    return retval


if __name__ == '__main__':
    # expose only one function to the cli
    setup(hug.API('cli'))
    # get_endpoints()
