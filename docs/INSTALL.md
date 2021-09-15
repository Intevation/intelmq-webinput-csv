**Table of Contents**

1. [Requirements](#requirements)
2. [Installation](#installation)
   * [Native packages](#native-packages)
   * [With pip](#with-pip)
     * [From PyPi](#from-pypi)
     * [From the repository](#from-the-repository)
3. [Afterwards](#afterwards)


Please report any errors you encounter at https://github.com/Intevation/intelmq-webinput-csv/issues

For upgrade instructions, see [UPGRADING.md](UPGRADING.md).

# Requirements

* An installed python3 [hug](https://www.hug.rest/)
* An installed [intelmq](https://intelmq.org) installation on the same machine.

# Installation

Please note that the pip3 installation method does not (and cannot) create /opt/intelmq/etc/examples/webinput_csv.conf.
As workaround you need to move the file from the site-packages directory to /opt/intelmq manually.
The location of this directory varies, it could be `/usr/lib/python3.4/site-packages`, `/usr/local/lib/python3.5/dist-packages/` or similar.

## From the repository

Clone the repository if not already done:
```bash
git clone https://github.com/Intevation/intelmq-webinput-csv.git
```

If you have a local repository and you have or will do local modification, consider using an editable installation (`pip install -e .`).
```
pip3 install .
```

### Webserver configuration and permissions

Configure your server to use the intelmq_webinput_csv executable as WSGI script. A configuration snippet for Apache can be found in `contrib/apache/002_intelmq_webinput_csv.conf`. Adapt the WSGIScriptAlias URL and path to your needs. On Debian systems the required wsgi package is called `libapache2-mod-wsgi-py3`

# Afterwards

Now continue with the [User Guide](User-Guide.md).
