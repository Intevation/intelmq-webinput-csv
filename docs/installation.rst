Installation Guide
==================

Table of Contents
-----------------

1. `Requirements <#requirements>`__
2. `Installation <#installation>`__

Please report any errors you encounter at
https://github.com/Intevation/intelmq-webinput-csv/issues

For upgrade instructions, see `UPGRADING.md <UPGRADING.md>`__.

Requirements
------------

Backend
~~~~~~~

-  An installed python3 `hug <https://www.hug.rest/>`__
-  An installed `intelmq <https://intelmq.org>`__ (>= 3.0.0)
   installation on the same machine.
-  Optional `sqlite3 <https://www.sqlite.org/>`__ for authentication

Frontend
~~~~~~~~

-  An installed `yarn <https://yarnpkg.com>`__

Installation
------------

Currently the only way to install Webinput-CSV is to clone the
repository and do a manual installation. The following steps will guide
through the installation from source.

1. Clone the repository

   .. code:: bash

      git clone https://github.com/Intevation/intelmq-webinput-csv.git

2. Install using pip3

   .. code:: bash

      cd intelmq-webinput-csv
      pip3 install .

3. Build the client

   Eventuelly adapt ``publicPath`` in ``client/vue.config.js`` to your
   needs if needed, e.g. ``'/intelmq-webinput/'``.

   .. code:: bash

      cd client
      yarn && yarn build

4. Configuration files

   Webinput-CSV is searching for config files in the following order:

   -  A file specified via environment variable
      (``WEBINPUT_CSV_CONFIG=/my/folder/webinput_csv.conf``)
   -  The IntelMQ config folder (``/etc/intelmq/`` or
      ``/opt/intelmq/etc`` depending on your installation)

5. **(Optional)** Authentication

   To integrate and activate the authentication for Webinput-CSV create
   a config file similar to `the
   example <../config/backend/webinput-session.conf>`__. Webinput-CSV is
   searching for session configs in the following order:

   -  A file specified via environment variable
      (``WEBINPUT_CSV_SESSION_CONFIG=/my/folder/webinput-session.conf``)
   -  The IntelMQ config folder (``/etc/intelmq/`` or
      ``/opt/intelmq/etc`` depending on your installation)

   The configured path to the sqlite3 database has to be read- and
   writeable by the user running the backend. If the file does not exist
   it will be created on startup.

   To insert users into the database, there is a script called
   ``webinput-adduser``.

6. Create Apache2 configuration

   Make sure the Apache2 (or intelmq or the configured) user has read
   access to the folders containing the front- and backend. A
   configuration snippet for Apache can be found in
   ``config/apache-example/003_intelmq_webinput_csv.conf``. Adapt the
   WSGIScriptAlias URL and path to your needs. On Debian systems the
   required wsgi package is called ``libapache2-mod-wsgi-py3``. For the
   backend the apache has to listen on port 8667. The path prefix for
   the backend must be used in the apache config!

The application is now available via browser on the machine and the
configured path prefix, e.g. http://localhost/intelmq-webinput
