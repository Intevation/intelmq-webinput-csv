User-Guide
==========

The Webinput-CSV can be started with default values and is fully usable
(except of the injection in the IntelMQ pipeline queue). Most parameters
for the input are available in the Frontend and are self explaining.

Configuration
-------------

There are three levels of parameters:

- internal defaults
- the configuration file
- parameters set explicitly by the web interface

The only parameter you should really care of is
``destination_pipeline_queue`` which is needed to submit data to
IntelMQ. There is no internal default.

Usual configuration parameters
------------------------------

-  ``prefix``: can only be a path. Needed if the program is run not in
   ``/`` but a sub-path.
-  ``intelmq``: the parameters in this array are used to set-up the
   intelmq pipeline. ``destination_pipeline_*`` inside the array can be
   used to configure the pipeline, see the user-guide of intelmq for
   details.
-  ``destination_pipeline_queue``: It is the queue/routing key to push
   the messages into if the user does not check *Validate/Submit with Bots*.
-  ``destination_pipeline_queue_formatted``: Optional, if true, the
   ``destination_pipeline_queue`` is formatted like a python format
   string with the event as ``ev``. E.g.
   ``"destination_pipeline_queue": "{ev[feed.provider]}.{ev[feed.name]}"``
-  ``custom_input_fields``: These fields are shown in the interface with
   the given default values, see also below.
-  ``constant_fields``: Similar to above, but not shown to the user and
   added to all processed events.
-  ``required_fields``: A list of IntelMQ field names. If set (not empty
   list), all lines need to have these fields, otherwise they are marked
   as invalid and not submitted to IntelMQ. Example:
   ``required_fields: ["time.source", "source.ip"]``
-  ``bots``: An optional directory of bot definitions with the same structure as
   IntelMQ's runtime configuration. If the Webinput user checks
   *Validate/Submit with Bots* in the Frontend, these bots will be used for data
   validation and submission. Needs to contain a processing chain of any number
   of experts and exactly one output bot.
   For validation, output bots are not called. For submission, only the output
   bot writes the data to the destination, the data is not additionally pushed
   to the redis queue as specified in the configuration parameter
   ``destination_pipeline_queue``.
   Example configuration:

   .. code:: json

      "bots": {
          "taxonomy": {
              "module": "intelmq.bots.experts.taxonomy.expert"
          },
          "url": {
              "module": "intelmq.bots.experts.url.expert"
          },
          "gethostbyname": {
              "module": "intelmq.bots.experts.gethostbyname.expert"
          },
          "sql": {
              "module": "intelmq_webinput_csv.sql_output",
              "parameters": {
                  "autocommit": false,
                  "engine": "postgresql",
                  "database": "eventdb",
                  "host": "intelmq-database",
                  "port": 5432,
                  "user": "intelmq",
                  "password": "secret",
                  "sslmode": "allow",
                  "table": "events"
              }
          }
      }

   Warning: If no SQL output bot is configured, and the user uses validation/submission
   with bots, no data will be written anywhere, neither to an IntelMQ pipeline,
   nor to the database!

Mailgen configuration parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``mailgen_config_file``: Optional path to the mailgen configuration
   file.
-  ``target_groups``: Configuration how the backend can query the
   available target groups. See below.
-  ``mailgen_multi_templates_enabled``: Enable the mutli-template editor.
   It shows all available templates, validates them during editing, allows
   a preview for each, with buttons for reset to the original state and the
   possibility to drop them from the current mailgen run.
   Additionally it allows the user to save the template to the disk and
   delete templates from the disk, resulting in a complete template editor
   for mailgen.
   If disabled, a single template input is show in the UI, which is fixed for
   all notifications.

Usage
-----

Empty lines are always ignored.

Parameters
~~~~~~~~~~

Upload
^^^^^^

-  delimiter
-  quotechar
-  escapechar
-  skip initial space: ignore whitespace after delimiter
-  has header: If checked, the first line of the file will be shown in
   the preview, but will not be used for submission.
-  skip initial N lines: number of lines (*after* the header) which
   should be ignored for preview and submission.

Preview
^^^^^^^

-  timezone: The timezone will only be added if there is no timezone
   detected in the existing value. Used for both time.source and
   time.observation.
-  dry run: sets classification type and identifier to ``test``

Custom Input fields
'''''''''''''''''''

The Custom Input fields are added to all individual events if not
present already.

-  classification type and identifier: default values to be added to
   rows which do not already have these values

Additional fields with default values are configurable.

.. _upload-1:

Upload
~~~~~~

To submit the data to intelmq click *Send*. All lines not failing will
be submitted.

After submission, the total number of submitted lines is given.

Integration with Mailgen
------------------------

In IntelMQ-setups, which use `IntelMQ Mailgen <http://intevation.github.io/intelmq-mailgen/>`__
to create and deliver
notifications to network owners, some additional tweaks add more value
and flexibility to the system.

Applying different bots on one-shot data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a typical IntelMQ setup, all collectors and parsers feed the data
into a consecutive queue of expert bots and finally into one or more
output bots. Running different bots (or the same bots but with other
parameters) may be necessary for one-shot data.

The parameter ``destination_pipeline_queue`` defines where the IntelMQ
Webinput injects the data into the IntelMQ pipeline.

Further, setting a unique attribute in the events itself (typically in
the ``extra`` or ``feed`` section) allows applying “switches” (like rail
switches) in the IntelMQ pipeline, by routing the one-shot data to
different bots. The configuration parameters ``constant_fields`` and
``custom_input_fields`` are ideal for achieving this. For example:

.. code:: json

       "constant_fields": {
           "feed.provider": "my-organization"
       }

If a CERTBund Rules expert may receive data from IntelMQ Webinput, but
should ignore it, a rule similar to this example can be used:

.. code:: python

   from intelmq_certbund_contact.rulesupport import Directive


   def determine_directives(context):
       if context.section == "destination":
           return
       feed = context.get("feed.name")
       if feed.startswith('oneshot-csv'):
           context.logger.info('Oneshot detected!')
           return True
       return

In this example ``feed.name = 'oneshot-csv'`` is the ignore-criteria.

Using a differing IntelMQ Mailgen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Normally the data from the normal IntelMQ pipeline and the one-shot data
end in the same database, resulting in a mix again. For sending the
notifications, IntelMQ Mailgen needs to filter by the criteria again
when querying the database.

The user can use two different mailgen-instance, a “normal” one and one
for the one-shot data. Two features are useful for this:

1. By default, intelmqcbmail loads and uses
   ``/etc/intelmq/intelmq-mailgen.conf``.

   intelmqcbmail has a command line parameter ``--config`` / ``-c`` to read
   alternative configuration files instead of the default
   ``/etc/intelmq/intelmq-mailgen.conf``.
   For example:

   .. code::

       > intelmqcbmail -c /etc/intelmq/intelmq-mailgen-oneshot.conf

   See for more details: https://github.com/Intevation/intelmq-mailgen#user-content-configuration

   IntelMQ Webinput can select a different configuration file for
   `intelmqmail` using the `mailgen_config_file` configuration parameter.
   For example:

   .. code:: json

      "mailgen_config_file": "/etc/intelmq/intelmq-mailgen-oneshot.conf"
2. The configuration parameter ``additional_directive_where``, adding
   additional conditions to the WHERE-clause of the SQL-statement for the
   directives:

   .. code:: json

      "additional_directive_where": "\"template_name\" = 'qakbot_provider'"

   It is also possible to filter by the event’s attributes. For this
   purpose, the events-table will be joined automatically.

   .. code:: json

      "additional_directive_where": "events.\"feed.provider\" = 'my-organization'"

   Filtering by events-data decreases the performance, it is recommended to
   use filters on the directives only when possible. Documentation:
   https://github.com/Intevation/intelmq-mailgen#user-content-database-1

Using different scripts (formats)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The mailgen configuration specific to Webinput can contain a different path to
other Mailgen scripts, for example:

.. code:: json

   "script_directory": "/opt/formats/oneshot"

In contrast to normal mailgen operation, webinput passes the assigned columns of
the input to the script as default table format.
The table format was in earlier versions of mailgen a mandatory parameter of
``context.mail_format_as_csv`` an defines which data columns the CSV attachment
of the e-mail notifications contains.
If the script does not by itself pass a table format to ``mail_format_as_csv``,
Mailgen uses the columns which the user assigned in the Webinput user interface.

Thus, the most simple mailgen script is:

.. code:: python

   def create_notifications(context):
       # always create notifications, never postpone
       return context.mail_format_as_csv(substitutions={})

Defining CSV attachment columns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The table format (also: format spec) defines which data fields of the entire
event data will be included in the CSV attachment file in the notifications.

Mailgen's behavior is described in `its documentation <http://intevation.github.io/intelmq-mailgen/scripts.html#format-spec-also-table-format>`_.

Webinput passes the name of the columns, which are assigned by the operator, to mailgen.

If the Mailgen scripts do not define any other format spec, the notifications will contain exactly the columns assigned by the operator.
If the Mailgen scripts do define a format spec, they take precedence.

Mailgen Templates
~~~~~~~~~~~~~~~~~

The CERTBund Rules expert bases its decision which Template to use
solely on the event itself. Additional information can be added by the
Webinput operator.

With system-defined templates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The templates are already configured on the server by the system
administrator and the Webinput Operator chooses influences/chooses which
template mailgen will use.

Add a new input field to the Webinput Configuration like this:

.. code:: json

       "custom_input_fields": {
           "extra.template_prefix": ""
       }

A rule of the CERTBund Contact rules expert may look like this:

.. code:: python

   def determine_directives(context):
       ...
       template = context.get("extra.template_prefix", "oneshot_fallback")
       # Remove the field
       context.pop("extra.template_prefix", None)
       add_directives_to_context(context, msm, template)
       return True

   ...

   def create_directive(notification_format, matter, target_group, interval, data_format):
       """
       This method creates Directives looking like:
       template_name: openportmapper_provider
       notification_format: vulnerable-service
       notification_interval: 86400
       data_format: openportmapper_csv_inline

       """
       return Directive(template_name=matter + "_" + target_group,
                        notification_format=notification_format,
                        event_data_format=data_format,
                        notification_interval=interval)

In this example, the template will be
``$event[extra.template_prefix]_$target_group``. More complex rules can
be used of course.

Keep in mind that the templates files need to exist beforehand.

With operator-defined templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Webinput operator can set the template directly in user interface
with the *Template* button in the *CSV Notifications* section. If the
template is not set using this field, the template is determined by
mailgen’s configured formats.

Starting Mailgen
~~~~~~~~~~~~~~~~

If ``mailgen_config_file`` is not set, mailgen loads the default
configuration file (``'/etc/intelmq/intelmq-mailgen.conf'``). Mailgen,
as always, additionally reads the user (the webserver user)
configuration file (``'~/.intelmq/intelmq-mailgen.conf'``).

The complete Mailgen workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To do the complete workflow of IntelMQ and Mailgen in the webinput:

-  configure all necessary IntelMQ bots

   -  any that you wish, plus
   -  CERTBund Contact Expert
   -  CERTBund Rules Expert
   -  SQL Output, with the special module
      ``intelmq_webinput_csv.sql_output``

-  correctly configure mailgen
-  setup the mailgen configuration in webinput

The Postgres connection user must have write access to the events and
directives tables (for event insertion).

Target groups
~~~~~~~~~~~~~

The target groups are a special variant of constant fields as the
available values depend on the result of an SQL query to the `fody
database <https://github.com/Intevation/intelmq-fody-backend>`__
(contactdb tags) and the users can select values from multiple-choice
checkboxes. The selected values are saved in the event field
``extra.target_groups``. The CERTBund Rules Expert’s rules can use this
information to generate the correct directives.

Configuring this feature works as follows:

.. code:: json

       "target_groups": {
           "database": {
               "host": "localhost",
               "user": "fody",
               "password": "secret",
               "dbname": "contactdb"
           },
           "tag_name_query": "SELECT tag_name FROM tag WHERE tag_name_id = 2",
           "tag_value_query": "SELECT tag_value FROM tag WHERE tag_name_id = 2 ORDER BY tag_value"
       }

The first value of the ``tag_name_query`` query is used as label for the input
field, e.g. *Target Group*.

The values of the ``tag_value_query`` define the possible input values for the
multiple-choice checkboxes.
