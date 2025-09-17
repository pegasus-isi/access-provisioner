#!/usr/bin/python3


import htcondor
import re
import sys
import time
import os

from datetime import datetime, timedelta


class HTCondor:

    last_query = -1
    collector = htcondor.Collector("pegasus.access-ci.org:9618")
    idle_job_ads = []


    def idle_cpu_jobs(self):
        self.query()
        count = 0
        for ad in self.idle_job_ads:
            if "RequestGPUs" not in ad or ad["RequestGPUs"] == 0:
                count += 1
        return count


    def idle_gpu_jobs(self):
        self.query()
        count = 0
        for ad in self.idle_job_ads:
            if "RequestGPUs" in ad and ad["RequestGPUs"] > 0:
                count += 1
        return count


    def query(self):
        '''
        query HTCondor and add up the idle job types
        '''

        now = int(datetime.now().timestamp())
        if now - self.last_query < 30:
            return
        self.last_query = now

        self.idle_job_ads = []
        try:
            schedd_ad = self.collector.locate(htcondor.DaemonTypes.Schedd, "pegasus.access-ci.org")
            schedd = htcondor.Schedd(schedd_ad)
            self.idle_job_ads = schedd.query(constraint="JobStatus == 1 && isUndefined(hpc_annex_name) && time() - EnteredCurrentStatus > 60 && time() - EnteredCurrentStatus < 8*60*60",
                                            projection=["ClusterId, ProcId, RequestGPUs"])
        except Exception as err:
            print(f"Unable to query: {err}")
            return


