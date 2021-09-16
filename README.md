# IntelMQ Webinput CSV

This is a rewrite of the Flask-based web interface for inserting CSV data
into intelmq's pipelines developed by certat. The rewrite uses hug in the
backend and bootstrap-vue for the Frontend.

## Table of Contents

1. [Installation](#how-to-install)
1. [User guide](#user-guide)
1. [Development](#development)
1. [Licence](#licence)
## How to Install

To get the Webinput-CSV up and running, clone the repo and use
```bash
$ pip3 install .
$ hug -f intelmq_webinput_csv/serve.py -p 8002
```

[//]: <> (TODO: Package installation)
[//]: <> (TODO: Apache integration)

For more details see the [Installation guide](./docs/INSTALL.md).

## User Guide

The Webinput-CSV can be started with default values and is fully usable (except
of the injection in the IntelMQ pipeline queue). Most
parameters for the input are available in the Frontend and are self explaining.

For detailed description of configuration and parameters see the [user guide](./docs/User-Guide.md).


## Development

hug provides an auto-refresh development mode when starting the application
using
```bash
$ hug -f intelmq_webinput_csv/serve.py -p 8002
```
Like hug, yarn provides this for the client using

```bash
$ cd client
$ yarn && yarn serve
```

For detailed developer information and how to develop with docker see [developer guide](./docs/Developers-Guide.md)

## Licence

This software is licensed under GNU Affero General Public License
version 3.
