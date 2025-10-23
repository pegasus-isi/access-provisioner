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
    
    max_cpu_instances = 1
    max_gpu_instances = 1
    if "MAX_CPU_INSTANCES" in os.environ:
        max_cpu_instances = int(os.environ["MAX_CPU_INSTANCES"])
    if "MAX_GPU_INSTANCES" in os.environ:
        max_gpu_instances = int(os.environ["MAX_GPU_INSTANCES"])

    while True:

        print("-----")

        jetstream2.clean()
        jetstream2.clean_dns()

        print("Instances:")
        insts = jetstream2.instances()
        for owner, inst in insts.items():
            print(f"  Owner: {owner:<30} {inst['cpu']:>3} CPU, {inst['gpu']:>3} GPU")
            
        print("Submitters:")
        submitters = condor.submitters()
        for owner, s in submitters.items():
            idle_cpu_jobs = s["idle_cpu_jobs"]
            idle_gpu_jobs = s["idle_gpu_jobs"]
            running_cpu_jobs = s["running_cpu_jobs"]
            running_gpu_jobs = s["running_gpu_jobs"]
            cpu_instances = 0
            gpu_instances = 0
            if owner in insts:
                cpu_instances = insts[owner]["cpu"]
                gpu_instances = insts[owner]["gpu"]
            print(f"  Owner: {owner:<30} CPU: {idle_cpu_jobs:>4} idle, {running_cpu_jobs:>4} running   GPU: {idle_gpu_jobs:>4} idle, {running_gpu_jobs:>4} running")

            # provision instances as needed
            if running_cpu_jobs < 5:
                if idle_cpu_jobs > 0 and cpu_instances < max_cpu_instances:
                    print("    Provisioning a CPU instance")
                    jetstream2.provision(owner, inst_type="cpu")

            if running_gpu_jobs < 5:
                if idle_gpu_jobs > 0 and gpu_instances < max_gpu_instances:
                    print("    Provisioning a GPU instance")
                    jetstream2.provision(owner, inst_type="gpu")

        time.sleep(30)

if __name__ == "__main__":
    main()

