"""
Tests for intelmq-webinput-csv
"""
from unittest import mock

from intelmq.lib.bot import Dict39
from hug import test

import intelmq_webinput_csv.serve
from .test_main import CONFIG

EXAMPLE_DATA_URL = [
    Dict39({'source.url': 'http://example.com/'})
]
EXAMPLE_DATA_URL_TYPE = [
    EXAMPLE_DATA_URL[0] | {'classification.type': 'undetermined'}
]
BOT_CONFIG = Dict39({
    'bots': {
        'url': {
            'module': 'intelmq.bots.experts.url.expert',
            }
        }
    })
BOTS_CONFIG = Dict39({
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
})
BOT_CONFIG_JINJA = Dict39({
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
})


def test_bot_library():
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
                           'messages': [EXAMPLE_DATA_URL[0] | {'source.fqdn': 'example.com', 'source.port': 80,
                                                               'source.urlpath': '/',
                                                               'protocol.application': 'http', 'protocol.transport': 'tcp',
                                                               'classification.identifier': 'test', 'classification.type': 'test',
                                                               'feed.code': 'oneshot',
                                                               'feed.provider': 'my-organization',
                                                               }]}


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
                           'messages': [EXAMPLE_DATA_URL[0] | {'source.fqdn': 'example',
                                                               'source.port': 80,
                                                               'source.urlpath': '/',
                                                               'protocol.application': 'http', 'protocol.transport': 'tcp',
                                                               'classification.taxonomy': 'other', 'classification.type': 'undetermined',
                                                               'classification.identifier': 'test',
                                                               'feed.code': 'oneshot',
                                                               'feed.provider': 'my-organization',
}]}


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
