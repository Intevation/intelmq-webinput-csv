#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2018 nic.at GmbH <wagner@cert.at>
# Copyright (c) 2021 Bundesamt für Sicherheit in der Informationstechnik
# Authors:
#   Sascha Wilde <wilde@intevation.de>
# SPDX-License-Identifier: AGPL-3.0
import os

from setuptools import find_packages, setup

exec(open(os.path.join(os.path.dirname(__file__),
                       'intelmq_webinput_csv/version.py')).read())  # defines __version__
setup(
    name='intelmq_webinput_csv',
    version=__version__,
    author='Intevation GmbH',
    author_email='info@intevation.de',
    maintainer='Raimund Renkert',
    maintainer_email='raimund.renkert@intevation.de',
    packages=find_packages(),
    install_requires=[
        'hug',
        ],
    license='AGPLv3',
    description='This is a simple web interface allowing the user to '
                'insert data into intelmq\'s pipelines interactively with '
                'preview from the parser.',

    keywords='incident handling cert csirt',
    scripts = ['webinput-adduser']
)
