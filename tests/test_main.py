"""
Tests for intelmq-webinput-csv

SPDX-FileCopyrightText: 2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
"""
from unittest import mock
from pathlib import Path
from os import environ
from hug import test

import intelmq_webinput_csv.serve


CONFIG_SIMPLE = {
    "intelmq": {
        "destination_pipeline_db": 2,
        # autodetect if this script is running standalone (-> localhost) or GitHub Actions;
        # or in intelmq-cb-mailgen-docker environment -> intelmq-redis
        "destination_pipeline_host": "intelmq-redis" if (Path('/.dockerenv').exists() and not environ.get('CI')) else "localhost",
        "destination_pipeline_port": 6379
    },
    "destination_pipeline_queue": "taxonomy-expert-webinput-queue",
    "prefix": "",
    "mailgen_config_file": "/etc/intelmq/intelmq-mailgen-webinput.conf",
    "mailgen_temporary_template_name": "webinput"
}
CONFIG = CONFIG_SIMPLE | {
    "constant_fields": {
        "feed.provider": "my-organization"
    },
    "custom_input_fields": {
        "classification.identifier": "test",
        "feed.code": "webinput",
        "feed.name": "webinput-csv",
        "extra.template_prefix": ""
    },
    "required_fields": ["source.ip", "source.as_name"],
}
EXAMPLE_DATA = [
    {'source.ip': '127.0.0.1', 'source.asn': '1'},
]
EXAMPLE_DATA_ASNAME = [
    {'source.ip': '127.0.0.1', 'source.asn': '1', 'source.as_name': 'Example AS'},
]
EXAMPLE_DATA_INVALID = [  # bad IP address
    {'source.ip': '1270.0.0.1', 'source.asn': '1'},
]


def test_classification_types():
    with mock.patch('webinput_session.session.skip_authentication', new=True) as mock_test:
        result = test.call('GET', intelmq_webinput_csv.serve, '/api/classification/types/', headers={'Authorization:': 'any'})
    assert result.status == '200 OK'


def test_required_fields():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new={'required_fields': ['foo']}):
            result = test.call('GET', intelmq_webinput_csv.serve, '/api/custom/required_fields/', headers={'Authorization:': 'any'})
    assert result.status == '200 OK'
    assert result.data == ['foo']


def test_preview():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                         'data': EXAMPLE_DATA_ASNAME,
                                                                                         'custom': {},  # TODO
                                                                                         'dryrun': True,
                                                                                         })
    assert result.status == '200 OK'
    assert result.data['input_lines_invalid'] == 0


def test_submit_auth_fail():
    """
    Assumes some users are required?
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': True,
                                                                                         'data': EXAMPLE_DATA,
                                                                                         'dryrun': True,
                                                                                         })
    assert result.status == '401 Unauthorized'


def test_submit_auth():
    with mock.patch('intelmq_webinput_csv.serve.session.session_store'):
        with mock.patch('webinput_session.session.skip_verify_user', new=True):
            with mock.patch('webinput_session.session.skip_authentication', new=True):
                with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
                    result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': True,
                                                                                                 'data': EXAMPLE_DATA,
                                                                                                 'dryrun': True,
                                                                                                 'custom': {}
                                                                                                 })
    assert result.status == '200 OK'


def test_constant_fields():
    with mock.patch('intelmq_webinput_csv.serve.PipelineFactory') as pipeline_mock:
        with mock.patch('webinput_session.session.skip_verify_user', new=True):
            with mock.patch('webinput_session.session.skip_authentication', new=True):
                with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
                    with mock.patch('intelmq_webinput_csv.serve.DateTime.generate_datetime_now') as now:
                        now.return_value = '1970-01-01T13:37:00+00:00'
                        result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': True,
                                                                                                     'data': EXAMPLE_DATA_ASNAME,
                                                                                                     'custom': {},  # TODO
                                                                                                     "constant_fields": {
                                                                                                         "feed.provider": "my-organization"
                                                                                                     },
                                                                                                     'dryrun': True,
                                                                                                     })
        pipeline_mock.create.assert_called()
        assert mock.call().send('{"source.ip": "127.0.0.1", "source.asn": 1, "source.as_name": "Example AS", "feed.provider": "my-organization", '
                                '"classification.type": "test", "classification.identifier": "test", "feed.code": "webinput", '
                                '"time.observation": "1970-01-01T13:37:00+00:00", "__type": "Event"}') in pipeline_mock.create.mock_calls
    assert result.status == '200 OK'
    assert result.data['input_lines_invalid'] == 0


def test_preview_invalid():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                         'data': EXAMPLE_DATA_INVALID,
                                                                                         'custom': {},  # TODO
                                                                                         'dryrun': True,
                                                                                         })
    assert result.status == '200 OK'
    assert result.data['input_lines_invalid'] == 1
    assert result.data['errors'] == {'0': {"source.ip": ["Failed to add data '1270.0.0.1' as field 'source.ip': "
                                                         "invalid value '1270.0.0.1' (<class 'str'>) for key 'source.ip'"]}}


def test_version():
    """
    Simple test for the version
    """
    result = test.call('GET', intelmq_webinput_csv.serve, '/api/version')
    assert result.status == '200 OK'
    assert '.' in result.data
    # should only contain one line of data
    assert '\n' not in result.data.strip()
