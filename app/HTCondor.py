#!/usr/bin/python3


import htcondor2
import re
import sys
import time
import os

from datetime import datetime, timedelta


class HTCondor:

    last_query = -1
    collector = htcondor2.Collector("pegasus.access-ci.org:9618")
    subs = {}


    def submitters(self):
        self.query()
        return self.subs


    def query(self):
        '''
        query HTCondor and add up the job types
        '''

        now = int(datetime.now().timestamp())
        if now - self.last_query < 30:
            return
        self.last_query = now

        self.subs = {}
        try:
            schedd_ad = self.collector.locate(htcondor2.DaemonTypes.Schedd, "pegasus.access-ci.org")
            schedd = htcondor2.Schedd(schedd_ad)
            ads = schedd.query(constraint="isUndefined(hpc_annex_name) && time() - EnteredCurrentStatus < 8*60*60",
                               projection=["Owner, ClusterId, JobStatus, ProcId, RequestGPUs"])
            for ad in ads:
                if ad["Owner"] not in self.subs:
                    s = {
                        "idle_cpu_jobs": 0,
                        "idle_gpu_jobs": 0,
                        "running_cpu_jobs": 0,
                        "running_gpu_jobs": 0
                    }
                    self.subs[ad["Owner"]] = s
                s = self.subs[ad["Owner"]]
                if ad["JobStatus"] == 1:
                    if "RequestGPUs" in ad and ad["RequestGPUs"] > 0:
                        s["idle_gpu_jobs"] += 1
                    else:
                        s["idle_cpu_jobs"] += 1
                elif ad["JobStatus"] == 2:
                    if "RequestGPUs" in ad and ad["RequestGPUs"] > 0:
                        s["running_gpu_jobs"] += 1
                    else:
                        s["running_cpu_jobs"] += 1
        except Exception as err:
            print(f"Unable to query: {err}")
            return


