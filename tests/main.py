"""
Tests for intelmq-webinput-csv
"""
from unittest import mock

from hug import test

import intelmq_webinput_csv.serve


CONFIG = {
    "intelmq": {
        "destination_pipeline_db": 2,
        "destination_pipeline_host": "intelmq-redis",
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
}
EXAMPLE_DATA = [
    {'source.ip': '127.0.0.1', 'source.asn': '1'},
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
                                                                                         'data': EXAMPLE_DATA,
                                                                                         'custom': {},  # TODO
                                                                                         'dryrun': True,
                                                                                         })
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
