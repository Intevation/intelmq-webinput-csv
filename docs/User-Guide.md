User-Guide
==========

Configuration
-------------

There are three levels of parameters:
 * internal defaults
 * the configuration file
 * parameters set explicitly by the webinterface

The only parameter you should really care of is `destination_pipeline_queue` which is
needed to submit data to IntelMQ. There is no internal default.

## Usual configuration parameters

* `prefix`: can only be a path.
  Needed if the program is run not in `/` but a sub-path.
* `intelmq`: the parameters in this array are used to set-up the intelmq pipeline. `destination_pipeline_*` inside the array can be used to configure the pipeline, see the user-guide of intelmq for details.
* `destination_pipeline_queue`: It is the queue/routing key to push the messages into.
* `destination_pipeline_queue_formatted`: Optional, if true, the `destination_pipeline_queue` is formatted like a python format string with the event as `ev`. E.g. `"destination_pipeline_queue": "{ev[feed.provider]}.{ev[feed.name]}"`
* `custom_input_fields`: These fields are shown in the interface with the given default values, see also below.
* `constant_fields`: Similar to above, but not shown to the user and added to all processed events.
* `required_fields`: A list of IntelMQ field names. If set (not empty list), all lines need to have these fields, otherwise they are marked as invalid and not submitted to IntelMQ. Example: `required_fields: ["time.source", "source.ip"]`

### Mailgen configuration parameters

* `mailgen_config_file`: Optional path to the mailgen configuration file.
* `mailgen_temporary_template_name`: Name of the temporary mailgen template.

Usage
-----

Empty lines are always ignored.

### Parameters

#### Upload

* delimiter
* quotechar
* escapechar
* skip initial space: ignore whitespace after delimiter
* has header: If checked, the first line of the file will be shown in the preview, but will not be used for submission.
* skip initial N lines: number of lines (*after* the header) which should be ignored for preview and submission.

#### Preview

* timezone: The timezone will only be added if there is no timezone detected in the existing value. Used for both time.source and time.observation.
* dry run: sets classification type and identifier to `test`

##### Custom Input fields
The Custom Input fields are added to all individual events if not present already.

* classification type and identifier: default values to be added to rows which do not already have these values

Additional fields with default values are configurable.

### Upload

To submit the data to intelmq click *Send*. All lines not failing will be submitted.

After submission, the total number of submitted lines is given.

Integration with Mailgen
------------------------

In IntelMQ-setups, which use IntelMQ Mailgen to create and deliver notifications to network owners, some additional tweaks add more value and flexibility to the system.

### Applying different bots on one-shot data

In a typical IntelMQ setup, all collectors and parsers feed the data into a consecutive queue of expert bots and finally into one or more output bots.
Running different bots (or the same bots but with other parameters) may be necessary for one-shot data.

The parameter `destination_pipeline_queue` defines where the IntelMQ Webinput injects the data into the IntelMQ pipeline.

Further, setting a unique attribute in the events itself (typically in the `extra` or `feed` section) allows applying "switches" (like rail switches) in the IntelMQ pipeline, by routing the one-shot data to different bots. The configuration parameters `constant_fields` and `custom_input_fields` are ideal for achieving this. For example:
```json
    "constant_fields": {
        "feed.provider": "my-organization"
    }
```

If a CERTBund Rules expert may receive data from IntelMQ Webinput, but should ignore it, a rule similar to this example can be used:
```python
from intelmq_certbund_contact.rulesupport import Directive


def determine_directives(context):
    if context.section == "destination":
        return
    feed = context.get("feed.name")
    if feed.startswith('oneshot-csv'):
        context.logger.info('Oneshot detected!')
        return True
    return
```
In this example `feed.name = 'oneshot-csv'` is the ignore-criteria.

### Using a differing IntelMQ Mailgen

Normally the data from the normal IntelMQ pipeline and the one-shot data end in the same database, resulting in a mix again. For sending the notifications, IntelMQ Mailgen needs to filter by the criteria again when querying the database.

The user can use two different mailgen-instance, a "normal" one and one for the one-shot data. Two features are useful for this:
1. intelmqcbmail has a command line parameter `--config` / `-c` to read alternative configuration files instead of the default `/etc/intelmq/intelmq-mailgen.conf`. For example:
   > intelmqcbmail -c /etc/intelmq/intelmq-mailgen-oneshot.conf
  See for more details: https://github.com/Intevation/intelmq-mailgen#user-content-configuration
2. The configuration parameter `additional_directive_where`, adding additional conditions to the WHERE-clause of the SQL-statement for the directives:
   ```sql
       "additional_directive_where": "\"template_name\" = 'qakbot_provider'"
   ```
   It is also possible to filter by the event's attributes. For this purpose, the events-table will be joined automatically.
   ```sql
       "additional_directive_where": "events.\"feed.provider\" = 'my-organization'"
   ```
   Filtering by events-data decreases the performance, it is recommended to use filters on the directives only when possible.
   Documentation: https://github.com/Intevation/intelmq-mailgen#user-content-database-1

### Mailgen Templates

The CERTBund Rules expert bases its decision which Template to use solely on the event itself.
Additional information can be added by the Webinput operator.

#### With system-defined templates

The templates are already configured on the server by the system administrator and the Webinput Operator chooses influences/chooses which template mailgen will use.

Add a new input field to the Webinput Configuration like this:
```json
    "custom_input_fields": {
        "extra.template_prefix": ""
    }
```

A rule of the CERTBund Contact rules expert may look like this:

```python
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

```

In this example, the template will be `$event[extra.template_prefix]_$target_group`.
More complex rules can be used of course.

Keep in mind that the templates files need to exist beforehand.

### With operator-defined templates

The Webinput operator can set the template directly in user interface with the *Template* button in the *CSV Content* section.
When clicking *Start Mailgen*, places the template under the file name configured in `mailgen_temporary_template_name` in mailgen's template path (parameter `template_dir` of mailgen).
For this to work, a mailgen *script* (also called *format*) must be active which sets the *template name* to the same value, for example:
```python
...

def create_notifications(context):
    return context.mail_format_as_csv(table_format, template_name='oneshot',
                                      substitutions={})
```

### Starting Mailgen

If `mailgen_config_file` is not set, mailgen loads the default configuration file (`'/etc/intelmq/intelmq-mailgen.conf'`).
Mailgen, as always, additionally reads the user (the webserver user) configuration file (`'~/.intelmq/intelmq-mailgen.conf'`).
