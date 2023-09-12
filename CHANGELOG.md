CHANGELOG
=========


1.2.1: UI Corrections (2023-09-12)
----------------------------------

## Frontend
- field assignment: disable buggy select on tab behaviour than the now missing fiel assignment with tab, see https://github.com/sagalbot/vue-select/issues/1797
- field assignment: enable autoscroll
- table: fixed column widths, prevent wobbling on interaction with vue-select element
- show overflows of vue-select elements


1.2.0: Single template input (2023-09-08)
-----------------------------------------

## Frontend
- Redesign to a single template input. The multi-template editor is hidden and can be activated with the parameter `mailgen_multi_templates_enabled`
- Pass assigned columns to the backend for notification preview and data submission
- Minor style enhancement in email preview
- Minor: add more spacing between the explanation text and the subject
- Target groups: add select all/none buttons
- Separate function for converting data to table

## Backend
- Allow single template input and pass to mailgen
- Do not send data to the redis queue if validation/submission with bots is active (would be a double-submit)
- Refactor format_spec creation, more checks/sanitation
- Template preview: use first line of data instead of fully relying on example data, use the first line of input data if available
- Use assigned columns as default table format: the columns assigned by the user in the frontend are used as default table format for mailgen
- Compatibility changes on deprecated pkg_resources / importlib replacement, make it compatible on both Ubuntu 20.04 and 22.04, update tests and GitHub Workflows

## Documentation
- Add section about the behaviour of the Frontend's "Submit/Validate with Bots" parameter


1.1.0: UI Enhancements (2023-08-21)
-----------------------------------

## Frontend
- Notification preview: decode quoted-printable email body
- Change the display of validation errors in table
  - color the row orange for errors in this row,
  - color a cell red for an error in this cell
  - color the Actions-cell (first column) red for an unspecific error (e.g. missing field) and show a tooltip
  - show the tooltip for cells only for errors on this cell
- Make Table more compact (smaller padding)
- Show small icon to show processed row instead of long text
- Add warning on duplicate field assignments after detection
- Link docs in navbar
- Clean field names for defaults from CSV header and for entered field names:
  - trim (remove surrounding whitespace)
  - all lower case
  - replace whitespaces with underscore
  - remove all other disallowed characters
- Field assignment selection: select on tab
- packages:
  - upgrade csv parser papaparse
  - replace obsolete babel polyfill with core-js
  - remove unused requirements mutationobserver-shim, popper.js, portal-vue

## Backend
- Data validation: group error messages for validation per field name in a row
- format row-process error log with newlines for easier readability
- only parse time-field if value is not empty
- read configfile with encoding

## Package
- build-depend on hug to run the tests during build
- set `NODE_OPTIONS=--openssl-legacy-provider`
- require either yarn or yarnpkg
- package dependency fixes

## Tests
- Add GitHub workflow to build debian packages
- Add GitHub workflow for pycodestyle

## Documentation
- Add GitHub workflow to build and publish documentation
- Ass missing change log sections for 1.0.0, 1.0.1, 1.0.2
- Add screenshots
- Switch from single Markdown files to Sphinx


1.0.2: Bugfixes (2023-08-10)
----------------------------

## Backend
- fix method arguments causing falcon errors
- remove obsolete, long-running DB queries
- fix falcon status code calls

## Frontend
- fix wrong modal on mailgen log button


1.0.1: Template Validations, UI optimizations (2023-08-10)
----------------------------------------------------------

## Frontend and Backend
- live feedback template syntax check
- template name validation

## Backend
- backend: verbose error message for empty template in preview

## Frontend
- improve default column field names
- template deletion safety question
- optimize UI components placement
- disable classification fields in dryrun


1.0.0: Mailgen Integration (2023-07-03)
---------------------------------------

  * Design and usability updates.
  * frontend: Cleanups and removal of deprecated single-template input field in favor of named templates.
  * frontend & backend: Previews per named template input group, using complete example data
  * backend: fixes


0.5.0 (2022-06-13)
------------------

## Backend
- Compatibility with only IntelMQ 3.0.0.

## Frontend
- Preview: removed the "selected" checkbox per column, the field selector is sufficient.
- ',' is the default delimiter.


0.4.1 (2021-10-02)
------------------

## Backend
- Renamed session package to `webinput_session` to avoid name clash with fodys session package


0.4.0 (2021-10-01)
------------------

## Backend
- Rewritten backend based on hug instead of flask.
- Session database and handling is identical to fody.

### Configuration
- New separate configuration file for the session configuration (`webinput-session.conf`).

### Documentation
- Updated installation documentation.

### Frontend
- Rewritten frontend based on bootstrap-vue.

### Packaging
- Added Debian packaging.


0.3.0 (unreleased)
------------------

## Backend
- For errors during parsing, also show the affected line after the traceback.
- Log which configuration file is read.


0.2.0 (2020-01-17)
------------------

### Backend
- Ignore header in total lines count. Also fixes the detection of IP-fields if only 2 lines are given and one line is the header.
- Auto-detect time-data, so frontend offers only time-related fields.
- Use static filename for uploaded data (#30).
- Basic parser error handling: In case of parse errors show the error message as preview table.
- Handle non-ASCII characters by using UTF-8 for all data (file) handling.
- Provide logger to the pipeline, supporting IntelMQ 2.0.
- Fix detection if a time value already has a timezone (did not work for negative postfixes like '-03:00').
- Do not throw errors on badly formatted time fields (#65).
- Add optional parameter `destination_pipeline_queue_formatted` and allow formatting of `destination_pipeline_queue`.
- Log exception if sending data to the pipeline did not work.
- For type-detection do not apply sanitation as this results in strange detections some times (#69).
- Save `raw` field including header for each event (#66).

### Configuration
- Do not use hardcoded `/opt/intelmq/` as base path, but intelmq's `CONFIG_DIR` (#61).
- The parameter `destination_pipeline_queue` is expected on the top level, not anymore in the `intelmq` array.

### Documentation
- More details and explanation on the configuration.
- Example apache configuration:
  - use intelmq user and group by default.
  - fix syntax and use own line for comments.
- Installation documentation: Add required wsgi package name.

### Frontend
- Better wording for maximum lines load/show (#59).

#### Preview

### Packaging
- setup: Fix path to example configuration file (#52).
- Add Manifest file (#62?)


0.1.0 (2018-11-21)
------------------

- Copyright and license header for each source code file.

### Backend
- Constant fields can be configured with the configuration parameter `"constant_fields"` (#38).
- Additional custom input fields can be added with the configuration parameter `"custom_input_fields"` (#48).
- New endpoint to download current file (#51).
- Error handling for reading the temp file.
- Handle if `use_column` parameter is not given by frontend.
- Handle `KeyExists` errors on validation.
- Extra fields handling:
  - Only create dictionary if it is not already one (#55).
  - Allow any `extra.*` fields, remove any workarounds (#50).

### Configuration
- Change `destination_pipeline` configuration, see NEWS file for a full example.

### Documentation
- Add a Developers Guide.

### Frontend
- Show version including link to upstream in footer (#49).
- Use Vue-Select for choosing the columns' fields, allows setting fields as `extra.*` (#50).
- Show the taxonomy resulting from the selected type (#45).

#### Preview
- Remove input field text, not handled anyway in backend.
- Order and group input fields (#46).

0.1.0.alpha2 (2018-03-15)
-------------------------

### Backend
- Fix count of total lines in case of missing newline at end of input
- Handle constant field `feed.code`.
- Use submission time as `time.observation` if not given in data.
- plugins (css and js) is now served by directly reading the files, more robust.
- classification/types now serves types along with taxonomy.

### Frontend
- Add input field for `feed.code`.

0.1.0.alpha1 (2017-08-29)
-------------------------

### Backend
- Uploading of files and text, saves data in temporary files
- Uploaded files are deleted explicitly at shutdown
- Use configuration file for destination pipeline and number of preview lines
- preview returns list of errors and total number of lines
- submit pushes the data into the destination pipeline
- timezone is added to data if not given explicitly
- add classification.{type,identifier} if not already existent
- add file bin/application.wsgi for running the application as wsgi
