"""
Tests for intelmq-webinput-csv

SPDX-FileCopyrightText: 2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
"""
from unittest import mock

from hug import test

import intelmq_webinput_csv.serve
from .test_main import CONFIG, CONFIG_SIMPLE

EXAMPLE_DATA_URL = [
    {'source.url': 'http://example.com/'}
]
EXAMPLE_DATA_URL_ASNAME = [
    {'source.url': 'http://example.com/', 'source.as_name': 'Example AS'}
]
EXAMPLE_DATA_URL_TYPE = [
    EXAMPLE_DATA_URL[0] | {'classification.type': 'undetermined'}
]
EXAMPLE_DATA_URL_PROCESSED = [EXAMPLE_DATA_URL[0] | {'source.fqdn': 'example.com', 'source.port': 80,
                                                     'source.urlpath': '/',
                                                     'protocol.application': 'http', 'protocol.transport': 'tcp',
                                                     'classification.identifier': 'test', 'classification.type': 'test',
                                                     'feed.code': 'webinput',
                                                     'feed.provider': 'my-organization',
                                                     }]
BOT_CONFIG = {
    'bots': {
        'url': {
            'module': 'intelmq.bots.experts.url.expert',
        }
    }
}
BOTS_CONFIG = {
    'bots': {
        'url': {
            'module': 'intelmq.bots.experts.url.expert',
        },
        'taxonomy': {
            'module': 'intelmq.bots.experts.taxonomy.expert'
        },
        'format-field': {
            'module': 'intelmq.bots.experts.format_field.expert',
            'parameters': {
            },
        },
        'remove-affix': {
            'module': 'intelmq.bots.experts.remove_affix.expert',
            'parameters': {
                'remove_prefix': False,
                'field': 'source.fqdn',
                'affix': '.com'
            }
        }
    }
}
BOTS_CONFIG_URL_IP = {
    'bots': {
        'url': {
            'module': 'intelmq.bots.experts.url.expert',
        },
        'taxonomy': {
            'module': 'intelmq.bots.experts.taxonomy.expert'
        },
        'gethostbyname': {
            'module': 'intelmq.bots.experts.gethostbyname.expert',
        }
    }
}
BOT_CONFIG_JINJA = {
    'bots': {
        'jinja': {
            'module': 'intelmq.bots.experts.jinja.expert',
            'parameters': {
                'fields': {
                    'feed.url': "{{ error! msg['source.fqdn'] | upper }}"
                }
            }
        }
    }
}


def test_process_bot():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOT_CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'data': EXAMPLE_DATA_URL,
                                                                                               'custom': {},
                                                                                               'dryrun': True})
    assert result.status == '200 OK'
    del result.data['messages'][0]['time.observation']
    assert 'URLExpertBot initialized with id url' in result.data['log']
    assert 'Bot initialization completed.' in result.data['log']
    del result.data['log']
    assert result.data == {'status': 'success',
                           'messages': EXAMPLE_DATA_URL_PROCESSED}


def test_process_bot_multi_messages():
    """
    test /api/bots/process/ with multiple bots and multiple messages
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOT_CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'data': EXAMPLE_DATA_URL * 2,
                                                                                               'custom': {},
                                                                                               'dryrun': True})
    assert result.status == '200 OK'
    del result.data['messages'][0]['time.observation']
    del result.data['messages'][1]['time.observation']
    assert 'URLExpertBot initialized with id url' in result.data['log']
    assert 'Bot initialization completed.' in result.data['log']
    del result.data['log']
    assert result.data == {'status': 'success',
                           'messages': EXAMPLE_DATA_URL_PROCESSED * 2}


def test_bots_library():
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOTS_CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'data': EXAMPLE_DATA_URL_TYPE,
                                                                                               'custom': {},
                                                                                               'dryrun': False})
    assert result.status == '200 OK'
    del result.data['messages'][0]['time.observation']
    assert 'RemoveAffixExpertBot initialized with id remove-affix' in result.data['log']
    assert 'Bot initialization completed.' in result.data['log']
    del result.data['log']
    assert result.data == {'status': 'success',
                           'notifications': [],
                           'messages': [EXAMPLE_DATA_URL[0] | {'source.fqdn': 'example',
                                                               'source.port': 80,
                                                               'source.urlpath': '/',
                                                               'protocol.application': 'http', 'protocol.transport': 'tcp',
                                                               'classification.taxonomy': 'other', 'classification.type': 'undetermined',
                                                               'classification.identifier': 'test',
                                                               'feed.code': 'webinput',
                                                               'feed.provider': 'my-organization',
                                                               }]}


def test_bots_library_time():
    """
    test /process with time-data
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOTS_CONFIG):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'data': [{'time.source': '2023-01-08 19:01:01'}],
                                                                                               'custom': {},
                                                                                               'dryrun': False,
                                                                                               'timezone': '+02:00'})
    assert result.status == '200 OK'
    del result.data['messages'][0]['time.observation']
    assert 'RemoveAffixExpertBot initialized with id remove-affix' in result.data['log']
    assert 'Bot initialization completed.' in result.data['log']
    del result.data['log']
    assert result.data == {'status': 'success',
                           'messages': [{'classification.identifier': 'test', 'classification.type': 'test',
                                         'classification.taxonomy': 'test', 'feed.code': 'webinput', 'feed.provider': 'my-organization',
                                         'time.source': '2023-01-08T17:01:01+00:00'}]}


def test_bot_exception():
    """
    When a bot raises an exception during Bot initialization
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOT_CONFIG_JINJA):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'data': EXAMPLE_DATA_URL,
                                                                                               })
    assert result.status == '200 OK'
    assert result.data['status'] == 'error'
    assert 'jinja2.exceptions.TemplateSyntaxError:' in result.data['log'] or 'intelmq.lib.exceptions.MissingDependencyError:' in result.data['log']


def test_preview_bots_messages():
    """
    test /api/upload with multiple bots and multiple messages
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG | BOTS_CONFIG_URL_IP):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                         'data': EXAMPLE_DATA_URL_ASNAME * 2,
                                                                                         'custom': {},  # TODO
                                                                                         'dryrun': True,
                                                                                         'validate_with_bots': True,
                                                                                         })
    assert result.status == '200 OK'
    assert result.data['input_lines_invalid'] == 0
    assert result.data['output_lines_invalid'] == 0
    assert result.data['errors'] == {}


def test_bot_process_raises():
    """
    assert that /process shows an error when a bot raises
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG |
                        {'bots': {
                            'raises': {
                                'module': 'tests.raises_expert'
                            }
                        }}):
            with mock.patch('intelmq_webinput_csv.serve.get_bot_module_name', new=lambda x: x):  # imported from intelmq.lib.utils
                result = test.call('POST', intelmq_webinput_csv.serve, '/api/bots/process/', body={'submit': False,
                                                                                                'data': [{'event_description.text': 'text'}],
                                                                                                'custom': {},
                                                                                                'dryrun': True,
                                                                                                'validate_with_bots': True,
                                                                                                })
    assert result.status == '200 OK'
    print(result.data)
    assert result.data['status'] == 'error'
    assert 'some random error' in result.data['log']


def test_bot_upload_invalid():
    """
    assert that /api/upload treats a line completely invalid if it only results in one event and the bot raises an error on this one event
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG |
                        {'bots': {
                            'raises': {
                                'module': 'tests.raises_expert'
                            }
                        }}):
            with mock.patch('intelmq_webinput_csv.serve.get_bot_module_name', new=lambda x: x):  # imported from intelmq.lib.utils
                result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                            'data': [{'event_description.text': 'text'}],
                                                                                            'custom': {},
                                                                                            'dryrun': True,
                                                                                            'validate_with_bots': True,
                                                                                            })
    assert result.status == '200 OK'
    print(result.data)
    assert result.data['input_lines_invalid'] == 1
    assert result.data['output_lines_invalid'] == 1
    assert 'some random error' in result.data['log']


def test_bot_upload_valid_with_one():
    """
    assert that /upload treats a line valid if one event from the line is valid
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG_SIMPLE |
                        {'bots': {
                            'splits': {
                                'module': 'tests.split_expert'
                            },
                            'raises': {
                                'module': 'tests.raises_expert'
                            }
                        }}):
            with mock.patch('intelmq_webinput_csv.serve.get_bot_module_name', new=lambda x: x):  # imported from intelmq.lib.utils
                result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                            'data': [{'event_description.text': 'text'}],
                                                                                            'custom': {},
                                                                                            'dryrun': True,
                                                                                            'validate_with_bots': True,
                                                                                            })
    assert result.status == '200 OK'
    print(result.data)
    assert result.data['input_lines_invalid'] == 0
    assert result.data['output_lines_invalid'] == 1
    assert 'some random error' in result.data['log']


def test_bot_empty_output_valid():
    """
    assert that if a bot returns no events (e.g. filtered), then the line is valid even if the output is empyt
    """
    with mock.patch('webinput_session.session.skip_authentication', new=True):
        with mock.patch('intelmq_webinput_csv.serve.CONFIG', new=CONFIG |
                        {'bots': {
                            'filter': {
                                'module': 'intelmq.bots.experts.filter.expert',
                                'parameters': {
                                    'filter_action': 'keep',
                                    'filter_key': 'source.ip',
                                    'filter_value': '127.0.0.1',
                                }
                            }
                        }}):
            result = test.call('POST', intelmq_webinput_csv.serve, '/api/upload/', body={'submit': False,
                                                                                         'data': [{'event_description.text': 'text'}],
                                                                                         'custom': {},
                                                                                         'dryrun': True,
                                                                                         'validate_with_bots': True,
                                                                                         })
    assert result.status == '200 OK'
    assert result.data['input_lines_invalid'] == 0
    assert result.data['output_lines_invalid'] == 0
