"""
A minimal setupfile for webinput_session.

SPDX-FileCopyrightText: 2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
"""

from setuptools import setup, find_packages

setup(
    name='intelmq-session',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.9.1.dev0',

    description='A hug based microservice api to intelmq.',

    packages=find_packages(),

    install_requires=['hug', 'psycopg2', 'python-dateutil'],

)
