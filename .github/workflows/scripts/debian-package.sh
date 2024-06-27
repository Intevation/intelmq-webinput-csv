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
echo "deb [signed-by=/etc/apt/trusted.gpg.d/sebix.asc] http://download.opensuse.org/repositories/home:/sebix:/intelmq/${os_repo_name}_${VERSION_ID}/ /" | sudo tee /etc/apt/sources.list.d/intelmq.list
sudo wget -O /etc/apt/trusted.gpg.d/sebix.asc https://download.opensuse.org/repositories/home:sebix:intelmq/${os_repo_name}_${VERSION_ID}/Release.key
echo "deb [signed-by=/etc/apt/trusted.gpg.d/nodesource.asc] https://deb.nodesource.com/node_14.x ${VERSION_CODENAME} main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo wget -O /etc/apt/trusted.gpg.d/nodesource.asc  https://deb.nodesource.com/gpgkey/nodesource.gpg.key
echo "deb [signed-by=/etc/apt/trusted.gpg.d/yarn.asc] https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarnpkg.list
sudo wget -O /etc/apt/trusted.gpg.d/yarn.asc https://dl.yarnpkg.com/debian/pubkey.gpg
sudo apt-get update

# install build dependencies
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get update -qq
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get install dpkg-dev lintian -y
DEBIAN_FRONTEND="noninteractive" sudo -E apt-get build-dep -y .

dpkg-buildpackage -us -uc -b
