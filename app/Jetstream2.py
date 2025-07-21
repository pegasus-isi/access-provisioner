#!/usr/bin/python3

import openstack
import re
import sys
import time
import os
import base64

from datetime import datetime, timedelta
from dateutil import parser, tz
from collections import defaultdict

from pprint import pprint


class Jetstream2:

    cloud = openstack.connect(cloud='openstack')
    token = None


    def __init__(self):
        # read the token - user the same one which is bind mounted to
        # /etc/condor/tokens.d/pegasus.access-ci.org.token
        with open("/etc/condor/tokens.d/pegasus.access-ci.org.token", "r") as f:
            self.token = f.read()


    def clean(self):

        for server in self.cloud.compute.servers():
            if not re.match('^testpool-', server.name):
                continue

            created_at = parser.parse(server.created_at, ignoretz=True)
            if not 'updated' in server:
                server.updated = server.created_at
            last_update = parser.parse(server.updated, ignoretz=True)
            now = datetime.utcnow()

            if server.status == 'SHUTOFF' or server.status == 'ERROR':
                # remove the server
                print(f"Deleting server {server.name}")
                self.cloud.delete_server(server.name)
                continue

            # sometimes the instances get stuck in BUILD state
            if server.status == 'BUILD' and created_at < now - timedelta(hours=2):
                # remove the server
                print(f"Deleting server {server.name}")
                self.cloud.delete_server(server.name)
                continue

            # just stuck
            if last_update < now - timedelta(days=30):
                # remove the server
                print(f"Instance seems stuck, deleting server {server.name}")
                self.cloud.delete_server(server.name)
                continue


    def instances(self):

        cpus = 0
        gpus = 0
        for server in self.cloud.compute.servers():

            if re.match('^testpool-cpu', server.name):
                cpus += 1
            
            if re.match('^testpool-gpu', server.name):
                gpus += 1

        return (cpus, gpus)


    def provision(self, inst_type="cpu"):

        flavor = "m3.large"
        start = "True"
        if inst_type == "gpu":
            flavor = "g3.medium"
            start = "TARGET.RequestGPUs > 0"

        now = int(datetime.now().timestamp())
        dt = datetime.now()
        now = str(dt.strftime('%Y%m%d%H%M%S'))
        name = f"testpool-{inst_type}-{now}"

        print(f"Creating new instance named {name}")

        userdata = f"""#!/bin/bash

cat >/etc/condor/config.d/50-testpool.conf <<EOF
# Allow any jobs on the TestPool
START = {start}

# advertise that is is the testpool
TestPool = True
STARTD_ATTRS = TestPool \$(STARTD_ATTRS)

# For workshops, keep resources around for longer
STARTD_NOCLAIM_SHUTDOWN = 2 * 60 * 60
EOF

cat >/etc/condor/tokens.d/access-pegasus.token <<EOF
{self.token}
EOF
chown root:root /etc/condor/tokens.d/access-pegasus.token
chmod 600 /etc/condor/tokens.d/access-pegasus.token

condor_reconfig

"""

        userdata = base64.b64encode(userdata.encode("utf-8")).decode("utf-8")

        #image = self.cloud.image.find_image("ACCESS-Pegasus-Worker", ignore_missing=False)
        image = self.cloud.image.find_image("98d9a658-9202-44c0-96d7-835c0f6fedda", ignore_missing=False)
        flavor = self.cloud.compute.find_flavor(flavor)
        network = self.cloud.network.find_network("auto_allocated_network")
        keypair = self.cloud.compute.find_keypair("rynge-2020")

        # need to reuse a floating IP
        #floating_ip = None
        #for fip in self.cloud.list_floating_ips():
        #    #print(fip)
        #    if re.match("^testpool", fip.description) and fip.status == "DOWN":
        #        floating_ip = fip
        #        break
        #if floating_ip == None:
        #    print("No floating IP found. Can't create new server")
        #    return

        server = self.cloud.compute.create_server(
            name=name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[{"uuid": network.id}],
            security_groups=[{"name": "default"}],
            key_name=keypair.name,
            user_data=userdata,
            wait=True
        )

        self.add_floating_ip(server.name)

    
    def add_floating_ip(self, server_name):

        timeout = int(datetime.now().timestamp()) + 60
        done = False
        server = None

        time.sleep(20)

        while not done and int(datetime.now().timestamp()) < timeout:
            server = self.cloud.get_server(server_name)
            if "addresses" in server:
                self.cloud.add_auto_ip(server, wait=True)
                done = True
            time.sleep(5)

        if not done:
            # unable to add the floating ip, delete the server
            self.cloud.delete_server(server.name)

    
