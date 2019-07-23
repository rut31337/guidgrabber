#!/usr/bin/python3

import json
import ravello_sdk
from common import *

import re
from requests.auth import HTTPBasicAuth

#Connect to Ravello
username,password = get_credentials()
client = connect(username, password)
if not client:
  exit (1)

app = client.get_applications()
print(json.dumps(app))
