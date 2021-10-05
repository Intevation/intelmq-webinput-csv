# IntelMQ Webinput CSV

A web interface for interactively inserting one-off CSV data into 
[IntelMQ](https://intelmq.org/)'s pipelines.

It is implemented in Python with [hug](https://www.hug.rest/) in the backend
and Javascript with bootstrap-vue in the frontend.
This is a rewrite of the original Flask-based web interface by CERT.at.

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
