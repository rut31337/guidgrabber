#!/usr/bin/python3

import argparse
import requests
import re
import json

#parser = argparse.ArgumentParser(description="Get Apps From Ravello")
#parser.add_argument('--ufilter', help='User To Filter Searches To', required=True, default=None)
#parser.add_argument('--session', help='Session', required=True, default=None)
#parser.add_argument('--labcode', help='Lab Code', required=True)
#args = parser.parse_args()
#
#userFilter = args.ufilter
#session = args.session
#labCode = args.labcode

def application_state(app):
    states = list(set((vm['state'] for vm in app.get('deployment', {}).get('vms', []))))
    return states if len(states) > 1 else states[0] if len(states) == 1 else None


def status(app,appname):
        status = application_state(app)
        #app_name = app['name'].encode('utf-8')
        print(status)

with open("apps.json", "r") as json_file:
  apps = json.load(json_file)
  #print(apps)
  appname = ""
  for app in apps:
    a = app['deployment']
    status(a,appname)
