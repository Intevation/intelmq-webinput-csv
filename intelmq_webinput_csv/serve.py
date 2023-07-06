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
from itertools import chain
from importlib import import_module
from pathlib import Path
from re import compile
from subprocess import run
from typing import Optional
from pkg_resources import get_distribution, resource_filename

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
from intelmq.lib.utils import load_configuration, LOG_FORMAT_STREAM
from intelmq.lib.datatypes import BotType, Dict39

from webinput_session import config, session
from intelmq_webinput_csv.sql_output import WebinputSQLOutputBot
try:
    from .data import EXAMPLE_CERTBUND_EVENT
except ImportError:  # attempted relative import with no known parent package
    exec(Path(__file__).with_name('data.py').read_text(encoding='utf-8'))

from psycopg2.extras import RealDictConnection, Json
from psycopg2 import connect, InterfaceError
from psycopg2.extensions import register_adapter

try:
    from intelmqmail import cb
    from intelmqmail.db import open_db_connection
except ImportError:
    cb = None


# automatic conversion of python dicts to postgres' json
register_adapter(dict, Json)
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

FILENAME_RE = compile('^[a-zA-Z0-9. _-]+$')


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
        try:
            bot = import_module(bot_config['module']).BOT
            kwargs = {}
            if bot is WebinputSQLOutputBot:
                kwargs = {'connection': conn}
            bots.append((bot_id, bot(bot_id, **kwargs, settings=BotLibSettings | bot_config.get('parameters', {}))))
        except Exception:
            return {'status': 'error',
                    'log': traceback.format_exc()}

    tracebacks = []
    input_lines_invalid = 0
    output_lines = 0
    output_lines_invalid = 0

    for lineno, item in enumerate(data):
        if not item:
            retval[lineno] = ('Line is empty', )
            continue

        event, input_line_valid = row_to_event(item, body, retval, lineno, time_observation)

        bots_input = [event]
        for bot_id, bot in bots:
            bot_raised_errors = False
            if bot.bottype is not BotType.OUTPUT:
                bots_output = []
            for message in bots_input:
                try:
                    queues = bot.process_message(message)
                except Exception:
                    bot_raised_errors = True
                    tracebacks.append(traceback.format_exc())
                    output_lines_invalid += 1
                else:
                    # for output bots, the output queue is empty, don't consider it
                    if bot.bottype is not BotType.OUTPUT:
                        bots_output.extend(queues['output'])
            # if > 0 errors and no valid messages, then the line is invalid
            if not bots_output and bot_raised_errors:
                input_line_valid = False
                break
            bots_input = bots_output
        if not bots:
            bots_output = [event]
        output_lines += len(bots_output)

        for event in bots_output:
            try:
                if CONFIG.get('destination_pipeline_queue_formatted', False):
                    CONFIG['destination_pipeline_queue'].format(ev=event)
            except Exception as exc:
                retval[lineno].append(f"Failed to generate destination_pipeline_queue {CONFIG['destination_pipeline_queue']}: {exc!s}")
                input_line_valid = False
            if not input_line_valid:
                continue

            if required_fields:
                diff = set(required_fields) - event.keys()
                if diff:
                    input_line_valid = False
                    retval[lineno].append(f"Line is missing these required fields: {', '.join(diff)}")

            # if 'raw' not in event:
            #     event.add('raw', ''.join(raw_header + [handle_rewindable.current_line]))
            raw_message = MessageFactory.serialize(event)
            if body.get('submit', True) and input_line_valid:
                destination_pipeline.send(raw_message)
            if not input_line_valid:
                input_lines_invalid += 1
        # if line was valid, increment the counter by 1
        input_lines_invalid += not input_line_valid

    output_lines_invalid = len(tracebacks)

    if body['dryrun'] and cb:
        conn.rollback()
    elif cb:
        conn.commit()

    # lineno is the index, for the number of lines add one
    total_lines = lineno + 1 if data else 0
    result = {"input_lines": total_lines,
              "input_lines_invalid": input_lines_invalid,
              "output_lines": output_lines,
              "output_lines_invalid": output_lines_invalid,
              "errors": retval}
    if tracebacks:
        result['log'] = '\n'.join(tracebacks)
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
    The target group is used by a rules expert's rule and is used here in the webinput as a special form of a constant field.
    """
    if 'target_groups' not in CONFIG:
        return {'tag_name': 'Target groups',
                'tag_values': []}
    conn = connect(**CONFIG['target_groups']['database'])
    cur = conn.cursor()
    cur.execute(CONFIG['target_groups']['tag_values_query'])
    tag_values = list(chain(*cur.fetchall()))
    cur.execute(CONFIG['target_groups']['tag_name_query'])
    tag_name = cur.fetchone()[0]
    return {'tag_name': tag_name,
            'tag_values': tag_values}


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
        return {"result": cb.start(mailgen_config, process_all=True, templates={item['name']: item['body'] for item in body.get('templates', [])}, dry_run=body.get('dry_run')),
                "log": mailgen_log.getvalue().strip()}
    except Exception:
        response.status = falcon.status.HTTP_500
        traceback.print_exc(file=sys.stderr)
        return {"result": str(traceback.format_exc()), "log": mailgen_log.getvalue().strip()}


@hug.post(ENDPOINT_PREFIX + '/api/mailgen/preview', requires=session.token_authentication)
def mailgen_preview(body, request, response):
    """
    Show mailgen email preview
    """
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
        conn.autocommit = False

        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO events ("{keys}") VALUES ({values})'
                        ''.format(keys='", "'.join(EXAMPLE_CERTBUND_EVENT.keys()),
                                values=', '.join(['%s'] * len(EXAMPLE_CERTBUND_EVENT))),
                        list(EXAMPLE_CERTBUND_EVENT.values()))
            cur.execute('START TRANSACTION')
            cur.execute('SELECT id FROM events')
            cur.execute('SELECT id, events_id FROM DIRECTIVES')
            cur.execute('SELECT id FROM directives ORDER BY id DESC LIMIT 1;')
            last_id = cur.fetchone()['id'] if cur.rowcount else None
            # ignore the additional_directive_where in mailgen config as that causes we are not seeing the test event
            additional_directive_where = f' d3.id >= {last_id}'

            return {"result": cb.start(mailgen_config, process_all=True,
                                       template=body.get('template'),
                                       get_preview=True,
                                       additional_directive_where=additional_directive_where,
                                       conn=conn)[0],  # only transmit the first notification
                    "log": mailgen_log.getvalue().strip()}
        finally:
            try:
                conn.rollback()
            except InterfaceError:  # connection already closed
                pass
    except Exception:
        log.exception('Mailgen Preview failed')  # also log it properly
        for line in mailgen_log.getvalue().splitlines():
            if line.startswith('ValueError: Invalid placeholder') or line.startswith('KeyError'):
                result = f'Validation failed: {line}'
                break
        else:
            result = traceback.format_exc()
        response.status = falcon.status.HTTP_500
        return {"result": result, "log": mailgen_log.getvalue()}


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
    log_handler.setFormatter(logging.Formatter(LOG_FORMAT_STREAM))

    conn = None

    if cb:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        conn = open_db_connection(mailgen_config, connection_factory=RealDictConnection)
        conn.autocommit = False
        # find the last directive ID before inserting our new ones
        cur = conn.cursor()
        cur.execute('SELECT id FROM directives ORDER BY id DESC LIMIT 1;')
        last_id = cur.fetchone()['id'] if cur.rowcount else None


    bots = []
    for bot_id, bot_config in CONFIG.get('bots', {}).items():
        try:
            logging.getLogger(bot_id).addHandler(log_handler)
            bot = import_module(bot_config['module']).BOT
            kwargs = {}
            if bot is WebinputSQLOutputBot:
                if not conn:
                    conn = connect(database=bot_config['parameters']['database'],
                                   user=bot_config['parameters']['user'],
                                   password=bot_config['parameters']['password'],
                                   host=bot_config['parameters']['host'],
                                   port=bot_config['parameters']['port'],
                                   connection_factory=RealDictConnection)
                    conn.autocommit = False
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

    tracebacks = []
    for bot_id, bot in bots:
        if bot.bottype is not BotType.OUTPUT:
            bots_output = []
        for message in bots_input:
            try:
                queues = bot.process_message(message)
            except Exception:
                tracebacks.append(traceback.format_exc())
            else:
                # for output bots, the output queue is empty, don't consider it
                if bot.bottype is not BotType.OUTPUT:
                    bots_output.extend(queues['output'])
        bots_input = bots_output
    if not bots:
        bots_output = bots_input

    retval = {'status': 'error' if (not bots_output and tracebacks) else 'success',
              'messages': bots_output,
              'log': '\n'.join(tracebacks + [bot_logs.getvalue()])}

    if cb:
        mailgen_log = io.StringIO()
        log_handler = logging.StreamHandler(stream=mailgen_log)
        logging.getLogger('intelmqmail').addHandler(log_handler)
        logging.getLogger('intelmqmail').setLevel(logging.DEBUG)

        # select only the new directives
        additional_directive_where = (mailgen_config['database'].get('additional_directive_where', '') + (' AND' if 'additional_directive_where' in mailgen_config['database'] else '') + f' d3.id > {last_id}') if last_id else None

        retval['log'] += mailgen_log.getvalue().strip()
        retval['notifications'] = cb.start(mailgen_config, process_all=True,
                                           templates={item['name']: item['body'] for item in body.get('templates', [])},
                                           get_preview=True,
                                           conn=conn,
                                           dry_run=True,
                                           additional_directive_where=additional_directive_where)
        # in dry_run, mailgen calls conn.rollback() itself

        retval['log'] += mailgen_log.getvalue()
    elif conn:
        # for the SQL output bot, if mailgen was not running
        conn.rollback()

    return retval


@hug.get(ENDPOINT_PREFIX + '/api/mailgen/templates', requires=session.token_authentication)
def get_templates():
    """
    Returns all defined mailgen templates
    """
    mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
    template_dir = Path(mailgen_config['template_dir'])
    retval = {}
    for template in template_dir.glob('*'):  # iterdir does not work here as that is recursive
        retval[template.name] = template.read_text()
    return retval


@hug.put(ENDPOINT_PREFIX + '/api/mailgen/template', requires=session.token_authentication)
def set_template(template_name: str, template_body: str, response):
    """
    Saves a template to disk
    """
    if not FILENAME_RE.match(template_name):
        response.status = falcon.HTTP_403
        return f'Filename does not match {FILENAME_RE.pattern!r}.'

    mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
    template_dir = Path(mailgen_config['template_dir'])
    Path(template_dir / template_name.strip()).write_text(template_body.strip(), encoding='utf8')


@hug.delete(ENDPOINT_PREFIX + '/api/mailgen/template', requires=session.token_authentication)
def delete_template(template_name: str, response):
    """
    Deletes a template from disk
    """
    if not FILENAME_RE.match(template_name):
        response.status = falcon.HTTP_403
        return f'Filename does not match {FILENAME_RE.pattern!r}.'

    mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
    template_dir = Path(mailgen_config['template_dir'])
    template_file = Path(template_dir / template_name.strip())
    if not template_file.exists():
        response.status = falcon.HTTP_404
        return f'Template {template_file!s} does not exist'

    template_file.unlink()


@hug.get(ENDPOINT_PREFIX + '/api/version')
def version():
    """
    Return the version of the backend
    """
    try:
        git_describe = run(['git', 'describe'], cwd=os.path.dirname(__file__), capture_output=True, check=False)
        if git_describe.returncode == 0:
            return git_describe.stdout.strip()
    except FileNotFoundError:
        pass
    return get_distribution('intelmq-webinput-csv').version


if __name__ == '__main__':
    # expose only one function to the cli
    setup(hug.API('cli'))
    # get_endpoints()
