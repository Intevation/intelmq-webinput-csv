#!/usr/bin/env python3
"""Provides an API for IntelMQ

Requires hug (http://www.hug.rest/)

Development: call like
  hug -f serve.py
  connect to http://localhost:8000/

Several configuration methods are shown within the code.

SPDX-FileCopyrightText: 2016, 2017, 2022-2024 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later

Software engineering by Intevation GmbH <https://intevation.de>

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
try:
    from importlib.metadata import version as importlib_version
except ImportError:  # Ubuntu 20.04 and Ubuntu 22.04 with Python 3.7-3.8 has issues with importlib.resources
    importlib_version = None
    from pkg_resources import get_distribution
try:
    import importlib.resources as importlib_resources
    importlib_resources.files  # Try to access relevant attribute, fails if importlib-resources is too old?
except (ImportError, AttributeError):  # Ubuntu 20.04 has no importlib.resources
    importlib_resources = None
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
from intelmq.lib.exceptions import InvalidValue, IntelMQException, InvalidKey
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
    from intelmqmail.tableformat import build_table_format
except ImportError:
    cb = None


# automatic conversion of python dicts to postgres' json
register_adapter(dict, Json)
try:
    HARMONIZATION_CONF = load_configuration(HARMONIZATION_CONF_FILE)
except ValueError:
    # Fallback to internal harmonization file
    if importlib_resources:  # Ubuntu 22.04
        HARMONIZATION_CONF = load_configuration(importlib_resources.files('intelmq') / 'etc/harmonization.conf')
    else:  # Ubuntu 20.04
        HARMONIZATION_CONF = load_configuration(resource_filename('intelmq', 'etc/harmonization.conf'))

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

configfiles = [
    Path(CONFIG_FILE),
    Path('/etc/intelmq/webinput_csv.conf')
]
if ENV_CONFIG_FILE:
    configfiles.insert(0, Path(ENV_CONFIG_FILE).resolve())

CONFIG = {}
for path in configfiles:
    if path and path.exists() and path.is_file():
        print(f"Loading config from {path}")
        with path.open(encoding='utf-8') as f:
            CONFIG = json.load(f)
            ENDPOINT_PREFIX = CONFIG.get('prefix', '/webinput')
            if ENDPOINT_PREFIX.endswith('/'):
                ENDPOINT_PREFIX = ENDPOINT_PREFIX[:-1]

CONSTANTS = CONFIG.get('constant_fields', '{}')
ALLOWED_EVENT_FIELDS = CONFIG.get('allowed_event_fields', {})
if ALLOWED_EVENT_FIELDS:
    EVENT_HARMONIZATION = {
        'event': {k: v for (k, v) in HARMONIZATION_CONF['event'].items() if k in ALLOWED_EVENT_FIELDS}
    }
else:
    EVENT_HARMONIZATION = HARMONIZATION_CONF
ALLOWED_EVENT_FIELDS = EVENT_HARMONIZATION['event'].keys()
FIELD_TEST_EVENT = Event(harmonization=EVENT_HARMONIZATION)

# 255 bytes is a safe maximum length to allow
FILENAME_RE = compile('^[a-zA-Z0-9. _-][a-zA-Z0-9. _-]{,254}$')

FALLBACK_ASSIGNED_COLUMNS = ("source.asn", "source.ip", "time.source", "source.port", "destination.ip", "destination.port", "destination.fqdn", "protocol.transport")


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
        retval = defaultdict(dict)

    event = Event()
    line_valid = True
    lineerrors = defaultdict(list)
    for key in item:
        value = item[key]
        if key.startswith('time.') and value:
            try:
                parsed = dateutil.parser.parse(value, fuzzy=True)
                if not parsed.tzinfo:
                    value += body['timezone']
                    parsed = dateutil.parser.parse(value)
                value = parsed.isoformat()
            except ValueError as exc:
                lineerrors[key].append(f"Failed to parse {value!r} as time for field {key!r}: {exc!s}")
                line_valid = False
        try:
            FIELD_TEST_EVENT.is_valid(key, None, sanitize=False)  # raises InvalidKey if key is not in list of allowed keys
            event.add(key, value)
        except IntelMQException as exc:
            lineerrors[key].append(f"Failed to add data {value!r} as field {key!r}: {exc!s}")
            line_valid = False
    for key, value in body['custom'].items():
        if key.startswith('custom_') and key[7:] not in event:
            key = key[7:]
            try:
                event.add(key, value)
            except InvalidValue as exc:
                lineerrors[-1].append(f"Failed to add data {value!r} as field {key!r}: {exc!s}")
                line_valid = False
    for key in CONSTANTS:
        if key not in event:
            try:
                event.add(key, CONSTANTS[key])
            except InvalidValue as exc:
                lineerrors[-1].append(f"Failed to add data {CONSTANTS[key]!r} as field {key!r}: {exc!s}")
                line_valid = False

    retval[lineno] = lineerrors

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

    for lineno, item in enumerate(data):
        if not item:
            retval[lineno] = {-1: ('Line is empty', )}
            continue

        event, input_line_valid = row_to_event(item, body, retval, lineno, time_observation)
        if not input_line_valid:
            input_lines_invalid += 1
            continue

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
                else:
                    # for output bots, the output queue is empty, don't consider it
                    if bot.bottype is not BotType.OUTPUT:
                        bots_output.extend(queues['output'])
            # if > 0 errors and no valid messages, then the line is invalid
            if not bots_output and bot_raised_errors:
                retval[lineno][-1].append(f"Bot {bot_id} raised an error. Please inspect the details with the magnifier symbol on the left.")
                input_line_valid = False
                break
            bots_input = bots_output
        if not bots:
            bots_output = [event]
        output_lines += len(bots_output)

        if not body.get('validate_with_bots', False):
            for event in bots_output:
                try:
                    if CONFIG.get('destination_pipeline_queue_formatted', False):
                        CONFIG['destination_pipeline_queue'].format(ev=event)
                except Exception as exc:
                    retval[lineno][-1].append(f"Failed to generate destination_pipeline_queue {CONFIG['destination_pipeline_queue']}: {exc!s}")
                    input_line_valid = False
                if not input_line_valid:
                    continue

                if required_fields:
                    diff = set(required_fields) - event.keys()
                    if diff:
                        input_line_valid = False
                        retval[lineno][-1].append(f"Line is missing these required fields: {', '.join(diff)}")

                # if 'raw' not in event:
                #     event.add('raw', ''.join(raw_header + [handle_rewindable.current_line]))
                raw_message = MessageFactory.serialize(event)
                if body.get('submit', True) and input_line_valid:
                    destination_pipeline.send(raw_message)

        # if line was valid, increment the counter by 1
        input_lines_invalid += not input_line_valid

        if not retval[lineno]:
            del retval[lineno]

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
    return ALLOWED_EVENT_FIELDS


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


@hug.get(ENDPOINT_PREFIX + '/api/mailgen/settings', requires=session.token_authentication)
def mailgen_settings():
    """
    Returns true/false if mailgen is installed on the system.
    """
    return {
        'multi_templates_enabled': CONFIG.get('mailgen_multi_templates_enabled', False),
        'default_template_name': CONFIG.get('mailgen_default_template_name')
    }


@hug.get(ENDPOINT_PREFIX + '/api/settings', requires=session.token_authentication)
def settings():
    """
    Returns some configuration options
    """
    return {
        'custom_workflow_default': CONFIG.get('custom_workflow_default', False),
        'allow_validation_override': CONFIG.get('allow_validation_override', True)
    }


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
        response.status = falcon.HTTP_500
        return {"result": "intelmqmail is not available on this system."}

    format_spec = build_format_spec(body.get('assigned_columns'))

    try:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        return {"result": cb.start(mailgen_config, process_all=True,
                                   template=body.get('template'),
                                   templates={item['name']: item['body'] for item in body.get('templates', [])},
                                   dry_run=body.get('dry_run'),
                                   default_format_spec=format_spec),
                "log": mailgen_log.getvalue().strip()}
    except Exception:
        response.status = falcon.HTTP_500
        traceback.print_exc(file=sys.stderr)
        return {"result": str(traceback.format_exc()), "log": mailgen_log.getvalue().strip()}


@hug.post(ENDPOINT_PREFIX + '/api/mailgen/preview', requires=session.token_authentication)
def mailgen_preview(body, request, response):
    """
    Show mailgen email preview
    """
    if not body.get('template'):  # empty string
        response.status = falcon.HTTP_422
        return {'result': 'Empty template', 'log': ''}

    if body.get('template_name') and not FILENAME_RE.match(body.get('template_name')):
        response.status = falcon.HTTP_422
        return {'result': f'Template name does not match regular expression {FILENAME_RE.pattern!r}.'}

    mailgen_log = io.StringIO()
    log_handler = logging.StreamHandler(stream=mailgen_log)
    logging.getLogger('intelmqmail').addHandler(log_handler)

    if body.get('verbose'):
        logging.getLogger('intelmqmail').setLevel(logging.DEBUG)
    else:
        logging.getLogger('intelmqmail').setLevel(logging.INFO)

    if cb is None:
        response.status = falcon.HTTP_500
        return {"result": "intelmqmail is not available on this system."}

    format_spec = build_format_spec(body.get('assigned_columns'))
    example_data = EXAMPLE_CERTBUND_EVENT.copy()
    user_data = Event()  # we can't use the allowed_event_fields setting here, as we also need to consider fields produced by bots
    # validate the user data so that we only have syntactically correct values
    # otherwise the database INSERT may fail because of incorrect types
    for key, value in body.get('data', {}).items():
        # we ignore errors here
        # the goal is to show a template preview and give feedback on the template, not on the data
        user_data.add(key, value, sanitize=True, overwrite=True, raise_failure=False)
    for key, value in CONSTANTS.items():
        user_data.add(key, value, sanitize=True, overwrite=True, raise_failure=False)
    example_data.update(user_data)  # TODO:
    # this converts extra-keys to a single dict, so the INSERT below works
    example_data = example_data.to_dict(jsondict_as_string=True)

    try:
        mailgen_config = cb.read_configuration(CONFIG.get('mailgen_config_file'))
        conn = open_db_connection(mailgen_config, connection_factory=RealDictConnection)
        conn.autocommit = False

        try:
            cur = conn.cursor()
            cur.execute('START TRANSACTION')
            cur.execute('INSERT INTO events ("{keys}") VALUES ({values})'
                        ''.format(keys='", "'.join(example_data.keys()),
                                  values=', '.join(['%s'] * len(example_data))),
                        list(example_data.values()))
            cur.execute('SELECT id FROM directives ORDER BY id DESC LIMIT 1;')
            last_id = cur.fetchone()['id'] if cur.rowcount else None
            # ignore the additional_directive_where in mailgen config as that causes we are not seeing the test event
            additional_directive_where = f' d3.id >= {last_id}'

            return {"result": cb.start(mailgen_config, process_all=True,
                                       template=body.get('template'),
                                       get_preview=True,
                                       additional_directive_where=additional_directive_where,
                                       conn=conn, default_format_spec=format_spec)[0],  # only transmit the first notification
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
        response.status = falcon.HTTP_500
        return {"result": result, "log": mailgen_log.getvalue()}


@hug.get(ENDPOINT_PREFIX + '/api/bots/available', requires=session.token_authentication)
def bots_available(body) -> dict:
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
        retval = {0: defaultdict(list)}
        first_message, line_valid = row_to_event(item, body, retval)
        if not line_valid:
            NEWLINE = '\n'  # SyntaxError: f-string expression part cannot include a backslash
            return {'status': 'error',
                    'log': f"Line was not valid:\n{NEWLINE.join(chain.from_iterable(retval[0].values()))}"}
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

        format_spec = build_format_spec(body.get('assigned_columns'))

        retval['log'] += mailgen_log.getvalue().strip()
        retval['notifications'] = cb.start(mailgen_config, process_all=True,
                                           template=body.get('template'),
                                           templates={item['name']: item['body'] for item in body.get('templates', [])},
                                           get_preview=True,
                                           conn=conn,
                                           dry_run=True,
                                           additional_directive_where=additional_directive_where,
                                           default_format_spec=format_spec)
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
    Saves a template to disk.
    Not allowed when mailgen_multi_templates_enabled is not true.
    """
    if not CONFIG.get('mailgen_multi_templates_enabled', False):
        response.status = falcon.HTTP_403
        return ('Multi templates and template editor is not enabled, saving templates not allowed. '
                'Please see the documentation on help to enable this feature.')

    if not FILENAME_RE.match(template_name):
        response.status = falcon.HTTP_403
        return f'Template name does not match regular expression {FILENAME_RE.pattern!r}.'

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
        return f'Template name does not match regular expression {FILENAME_RE.pattern!r}.'

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
    if importlib_version:
        return importlib_version('intelmq-webinput-csv')
    else:
        return get_distribution('intelmq-webinput-csv').version


def build_format_spec(assigned_columns: Optional[list] = None) -> 'TableFormat':
    """
    If assigned_columns in the request is null or an empty array, use the fallback

    """
    assigned_columns = list(filter(None, assigned_columns))  # filter empty strings
    assigned_columns = assigned_columns if assigned_columns else FALLBACK_ASSIGNED_COLUMNS
    return build_table_format("Webinput Fallback",
                              tuple(((field, field) for field in assigned_columns if field)))


@hug.post(ENDPOINT_PREFIX + '/api/harmonization/fieldname_validity')
def check_fieldname_validity(fieldname: str):
    """
    Check if a field name is valid
    """
    try:
        FIELD_TEST_EVENT.is_valid(fieldname, None)
    except InvalidKey as exc:
        return {"status": False, "reason": str(exc)}
    else:
        return {"status": True}


if __name__ == '__main__':
    # expose only one function to the cli
    setup(hug.API('cli'))
    # get_endpoints()
