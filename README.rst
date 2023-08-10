IntelMQ Webinput CSV
====================

A web interface for interactively inserting one-off CSV data into
`IntelMQ <https://intelmq.org/>`__’s pipelines.

It is implemented in Python with `hug <https://www.hug.rest/>`__ in the
backend and Javascript with bootstrap-vue in the frontend. This is a
rewrite of the original Flask-based web interface by CERT.at.

Table of Contents
-----------------

1. `Installation <#how-to-install>`__
2. `User guide <#user-guide>`__
3. `Development <#development>`__
4. `Licence <#licence>`__

How to install
--------------

To get the Webinput-CSV up and running, clone the repo and use

.. code:: bash

   $ pip3 install .
   $ hug -f intelmq_webinput_csv/serve.py -p 8002

For more details see the `Installation guide <./docs/INSTALL.md>`__.

User Guide
----------

The Webinput-CSV can be started with default values and is fully usable
(except of the injection in the IntelMQ pipeline queue). Most parameters
for the input are available in the Frontend and are self explaining.

For detailed description of configuration and parameters see the `user
guide <./docs/User-Guide.md>`__.

Development
-----------

hug provides an auto-refresh development mode when starting the
application using

.. code:: bash

   $ hug -f intelmq_webinput_csv/serve.py -p 8002

Like hug, yarn provides this for the client using

.. code:: bash

   $ cd client
   $ yarn && yarn serve

For detailed developer information and how to develop with docker see
`developer guide <./docs/Developers-Guide.md>`__

Licence
-------

This software is licensed under GNU Affero General Public License
version 3.
