#!/usr/bin/python3

import re
import sys
import time
import os

from datetime import datetime, timedelta
from dateutil import parser, tz
from collections import defaultdict
from pprint import pprint

from HTCondor import *
from Jetstream2 import *

def main():

    print("Starting up...")

    condor = HTCondor()
    jetstream2 = Jetstream2()

    while True:

        print("-----")

        jetstream2.clean()

        cpu_instances, gpu_instances = jetstream2.instances()
        print(f"Instances: {cpu_instances} CPU, {gpu_instances} GPU")

        idle_cpu_jobs = condor.idle_cpu_jobs()
        idle_gpu_jobs = condor.idle_gpu_jobs()
        print(f"Idle jobs: {idle_cpu_jobs} CPU, {idle_gpu_jobs} GPU")
    
        if idle_cpu_jobs > 0 and cpu_instances < 2:
            print("Provisioning a CPU instance")
            jetstream2.provision(inst_type="cpu")

        if idle_gpu_jobs > 0 and gpu_instances < 2:
            print("Provisioning a GPU instance")
            jetstream2.provision(inst_type="gpu")

        time.sleep(30)

if __name__ == "__main__":
    main()

