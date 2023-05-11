# -*- coding: utf-8 -*-
"""
SPDX-FileCopyrightText: 2017-2018 nic.at GmbH <wagner@cert.at>, 2021-2022 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
Authors:
  Sascha Wilde <wilde@intevation.de>
"""
import os

from setuptools import setup

exec(open(os.path.join(os.path.dirname(__file__),
                       'intelmq_webinput_csv/version.py')).read())  # defines __version__
setup(
    name='intelmq_webinput_csv',
    version=__version__,
    author='Intevation GmbH',
    author_email='info@intevation.de',
    maintainer='Raimund Renkert',
    maintainer_email='raimund.renkert@intevation.de',
    packages=[
        'intelmq_webinput_csv',
        'webinput_session',
    ],
    install_requires=[
        # 'intelmq' is not listed here as this causes a re-installation of intelmq on development installations
        # https://github.com/pypa/pip/issues/10805
        'hug',
        ],
    license='AGPLv3',
    description='This is a simple web interface allowing the user to '
                'insert data into intelmq\'s pipelines interactively with '
                'preview from the parser.',

    keywords='incident handling cert csirt',
    scripts=['webinput-adduser'],
)
