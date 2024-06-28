#!/bin/bash

set -e

# put secrets in the right locations
mkdir -p ~/.condor/tokens.d
mkdir -p /etc/condor/tokens.d
mkdir -p ~/.config/openstack
cp -L /secrets/idtoken /etc/condor/tokens.d/pegasus.access-ci.org.token
chmod 600 /etc/condor/tokens.d/pegasus.access-ci.org.token
cp -L /secrets/idtoken ~/.condor/tokens.d/pegasus.access-ci.org.token
chmod 600 ~/.condor/tokens.d/pegasus.access-ci.org.token
cp -L /secrets/clouds-yaml ~/.config/openstack/clouds.yaml
chmod 600 ~/.config/openstack/clouds.yaml


echo
echo
condor_token_list
echo
echo

echo "Activating venv..."
. /venv/bin/activate

echo "Starting app..."
cd /app
python3 -u main.py 2>&1 | tee /app/log


