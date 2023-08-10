.. SPDX-FileCopyrightText: 2016, 2017, 2022-2023 Bundesamt für Sicherheit in der Informationstechnik
   SPDX-License-Identifier: AGPL-3.0-or-later

   Software engineering by Intevation GmbH <https://intevation.de>

Welcome to IntelMQ Webinput CSV documentation!
==============================================

A web interface for interactively inserting one-off CSV data to
`IntelMQ <https://intelmq.org/>`__ and `n6 <https://n6.readthedocs.io/>`__.

It is implemented in Python with `hug <https://www.hug.rest/>`__ in the
backend and Javascript with bootstrap-vue in the frontend. This is a
rewrite of the original Flask-based web interface by CERT.at.

Contents:

.. toctree::
   :maxdepth: 2

   installation
   user-guide.rst
   upgrade.rst
   developers-guide
   webinput-n6.rst

Screenshots
-----------

CSV Data Input
~~~~~~~~~~~~~~

.. figure:: ./images/csv-input.png
   :alt: CSV data insertion and parsing options

Data Validation
~~~~~~~~~~~~~~~

Assign data columns to IntelMQ fields and validate the data:

.. figure:: ./images/data-validation.png
   :alt: field asssignment and data validation

Data Row preview
~~~~~~~~~~~~~~~~

Preview the resulting parsed data per row including the complete IntelMQ processing log:

.. figure:: ./images/row-log-preview.png

Preview the resulting IntelMQ Mailgen notification

.. figure:: ./images/row-notification-preview.png

Mailgen Templates management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

View and modify all IntelMQ Mailgen templates including live validation:

.. figure:: ./images/templates.png


Licence
-------

This software is licensed under GNU Affero General Public License
version 3.
