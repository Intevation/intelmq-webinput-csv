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
import json
import os
import logging
from session import config, session
from intelmq import HARMONIZATION_CONF_FILE, CONFIG_DIR, VAR_STATE_PATH
from intelmq.lib.harmonization import DateTime, IPAddress
from intelmq.bots.experts.taxonomy.expert import TAXONOMY

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

@hug.startup()
def setup(api):
    log.debug(os.environ.get("WEBINPUT_CSV_SESSION_CONFIG"))
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
    log.debug(body)
    return
@hug.get(ENDPOINT_PREFIX + '/api/classification/types', requires=session.token_authentication)
def classification_types():
    return TAXONOMY


@hug.get(ENDPOINT_PREFIX + '/api/harmonization/event/fields', requires=session.token_authentication)
def harmonization_event_fields():
    return EVENT_FIELDS['event']

#  TODO for now show the full api documentation that hug generates
# @hug.get("/")
# def get_endpoints():
#     return ENDPOINTS


if __name__ == '__main__':
    # expose only one function to the cli
    setup(hug.API('cli'))
    # get_endpoints()
