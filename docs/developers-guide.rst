Developers Guide
================

Run locally
-----------

Backend
~~~~~~~

.. code:: bash

   WEBINPUT_CSV_SESSION_CONFIG=/path/to/config.file hug -f intelmq_webinput_csv/serve.py -p 8002

IntelMQ needs to be installed, as it is a dependency.

Frontend
~~~~~~~~

.. code:: bash

   yarn run dev

Using docker
------------

See
https://github.com/Intevation/intelmq-cb-mailgen-docker#user-content-scenario-2-development-dev

Release a new version
---------------------

- Document the changes in the `CHANGELOG.md`
-  make a changelog entry in ``debian/changelog`` using ``dch`` command
   line tool. don’t forget the revision
-  set ``clientVersion`` in ``client/src/components/WebinputCSV.vue``
-  set ``__version_info__`` in ``intelmq_webinput_csv/version.py``
-  make a commit and create a tag from it
