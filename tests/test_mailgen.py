"""
Tests for intelmq-webinput-csv mailgen parts

SPDX-FileCopyrightText: 2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
"""
from json import dumps
from unittest import mock
from hug import test

import intelmq_webinput_csv.serve


def test_delete_template_invalid_filename():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        result = test.call('DELETE', intelmq_webinput_csv.serve, '/api/mailgen/template', body={'template_name': '/etc/passwd'})
    assert result.status == '403 Forbidden'


def test_save_template_invalid_filename():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        result = test.call('PUT', intelmq_webinput_csv.serve, '/api/mailgen/template', body=dumps({'template_name': '/etc/passwd',
                                                                                                   'template_body': ''}), headers={"content-type": "application/json"})
    assert result.status == '403 Forbidden'
