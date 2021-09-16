#!/usr/bin/env python3
"""Provides an API for IntelMQ

Requires hug (http://www.hug.rest/)

Development: call like
  hug -f serve.py
  connect to http://localhost:8000/

Several configuration methods are shown within the code.


Copyright (C) 2016, 2017 by Bundesamt für Sicherheit in der Informationstechnik

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
    * Raimund Renkert<raimund.renkert@intevation.de>
"""

import hug
import dateutil.parser
import json
import os
import logging
from pathlib import Path
from session import config, session
from intelmq import HARMONIZATION_CONF_FILE, CONFIG_DIR
from intelmq.lib.pipeline import PipelineFactory
from intelmq.lib.harmonization import DateTime, IPAddress
from intelmq.lib.message import Event, MessageFactory
from intelmq.bots.experts.taxonomy.expert import TAXONOMY
from intelmq.lib.exceptions import InvalidValue, KeyExists

with open(HARMONIZATION_CONF_FILE) as handle:
    EVENT_FIELDS = json.load(handle)

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

class PipelineParameters(object):
    def __init__(self):
        for key, value in CONFIG['intelmq'].items():
            setattr(self, key, value)


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

@hug.post(ENDPOINT_PREFIX + '/api/upload', requires=session.token_authentication)
def uploadCSV(body, request, response):
    destination_pipeline = PipelineFactory.create(PipelineParameters(),
                                                logger=log,
                                                direction='destination')
    if not CONFIG.get('destination_pipeline_queue_formatted', False):
        destination_pipeline.set_queues(CONFIG['destination_pipeline_queue'], "destination")
        destination_pipeline.connect()
    time_observation = DateTime().generate_datetime_now()

    data = body["data"]
    customs = body["custom"]
    retval = []
    col = 0;
    line = 0;
    lines_valid = 0
    for item in data:
        event = Event()
        # Ensure dryrun has priority
        if body['dryrun']:
            event.add('classification.identifier', 'test')
            event.add('classification.type', 'test')
        for key in item:
            line_valid = True
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
                except (InvalidValue, KeyExists) as exc:
                    retval.append((key, value, str(exc)))
                    line_valid = False
                col = col+1
        for key in CONSTANTS:
            if key not in event:
                try:
                    event.add(key, CONSTANTS[key])
                except InvalidValue as exc:
                    retval.append((key, CONSTANTS[key], str(exc)))
                    line_valid = False
        for key in customs:
            if not key.startswith('custom_'):
                continue
            if key[7:] not in event:
                try:
                    event.add(key[7:], customs[key])
                except InvalidValue as exc:
                    retval.append((key, customs[key], str(exc)))
                    line_valid = False
        try:
            if CONFIG.get('destination_pipeline_queue_formatted', False):
                CONFIG['destination_pipeline_queue'].format(ev=event)
        except Exception as exc:
            retval.append((line, -1,
                            CONFIG['destination_pipeline_queue'], repr(exc)))
            line_valid = False
        if line_valid:
            lines_valid += 1
        line = line+1
        if 'classification.type' not in event:
            event.add('classification.type', 'test')
        if 'classification.identifier' not in event:
            event.add('classification.identifier', 'test')
        if 'feed.code' not in event:
            event.add('feed.code', 'oneshot')
        if 'time.observation' not in event:
            event.add('time.observation', time_observation, sanitize=False)
        # if 'raw' not in event:
        #     event.add('raw', ''.join(raw_header + [handle_rewindable.current_line]))
        raw_message = MessageFactory.serialize(event)
        destination_pipeline.send(raw_message)
    retval = {"total": line,
              "lines_invalid": line-lines_valid,
              "errors": retval}
    return retval

@hug.get(ENDPOINT_PREFIX + '/api/classification/types', requires=session.token_authentication)
def classification_types():
    return TAXONOMY


@hug.get(ENDPOINT_PREFIX + '/api/harmonization/event/fields', requires=session.token_authentication)
def harmonization_event_fields():
    return EVENT_FIELDS['event']

@hug.get(ENDPOINT_PREFIX + '/api/custom/fields', requires=session.token_authentication)
def custom_fields():
    return CONFIG.get('custom_input_fields', '{}')

#  TODO for now show the full api documentation that hug generates
# @hug.get("/")
# def get_endpoints():
#     return ENDPOINTS


if __name__ == '__main__':
    # expose only one function to the cli
    setup(hug.API('cli'))
    # get_endpoints()
