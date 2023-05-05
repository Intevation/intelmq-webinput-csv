"""
Tests for intelmq-webinput-csv
"""
from unittest import mock
from pathlib import Path
from os import environ
from hug import test

from intelmq.lib.bot import Dict39

import intelmq_webinput_csv.serve


# to use the | operator to merge dicts in Python < 3.9, use this compatibility class
CONFIG = Dict39({
    "intelmq": {
        "destination_pipeline_db": 2,
        # autodetect if this script is running standalone (-> localhost) or GitHub Actions;
        # or in intelmq-cb-mailgen-docker environment -> intelmq-redis
        "destination_pipeline_host": "intelmq-redis" if (Path('/.dockerenv').exists() and not environ.get('CI')) else "localhost",
        "destination_pipeline_port": 6379
    },
    "destination_pipeline_queue": "taxonomy-expert-oneshot-queue",
    "prefix": "",
    "constant_fields": {
        "feed.provider": "my-organization"
    },
    "custom_input_fields": {
        "classification.identifier": "test",
        "feed.code": "oneshot",
        "feed.name": "oneshot-csv",
        "extra.template_prefix": ""
    },
    "required_fields": ["source.ip", "source.as_name"],
    "mailgen_config_file": "/etc/intelmq/intelmq-mailgen-oneshot.conf",
    "mailgen_temporary_template_name": "oneshot"
})
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
    assert result.data['lines_invalid'] == 0


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
                                '"classification.type": "test", "classification.identifier": "test", "feed.code": "oneshot", '
                                '"time.observation": "1970-01-01T13:37:00+00:00", "__type": "Event"}') in pipeline_mock.create.mock_calls
    assert result.status == '200 OK'
    assert result.data['lines_invalid'] == 0


def test_preview_invalid():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                         'data': EXAMPLE_DATA_INVALID,
                                                                                         'custom': {},  # TODO
                                                                                         'dryrun': True,
                                                                                         })
    assert result.status == '200 OK'
    assert result.data['lines_invalid'] == 1
    assert result.data['errors'] == {'0': ["Failed to add data '1270.0.0.1' as field 'source.ip': "
                                           "invalid value '1270.0.0.1' (<class 'str'>) for key 'source.ip'"]}
