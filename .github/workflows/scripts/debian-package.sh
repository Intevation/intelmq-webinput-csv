#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2023 Intevation GmbH
# SPDX-License-Identifier: AGPL-3.0-or-later
#

set -xeu -o pipefail

# defines $ID, $VERSION_ID
. /etc/os-release

if [ "$ID" == "debian" ]; then
    os_repo_name="Debian"
elif [ "$ID" == "ubuntu" ]; then
    os_repo_name="xUbuntu"
fi
echo "deb http://download.opensuse.org/repositories/home:/sebix:/intelmq/${os_repo_name}_${VERSION_ID}/ /" > /etc/apt/sources.list.d/intelmq.list
wget -O - https://download.opensuse.org/repositories/home:sebix:intelmq/${os_repo_name}_${VERSION_ID}/Release.key | apt-key add -
echo "deb https://deb.nodesource.com/node_14.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list
wget -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarnpkg.list
wget -O - https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
apt update

# install build dependencies
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get update -qq
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get install dpkg-dev lintian -y
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get build-dep -y .

dpkg-buildpackage -us -uc -b
