#!/usr/bin/python3

import argparse
import requests
import urllib.parse
import time

import re
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(description="Get Services From CloudForms")
parser.add_argument('--cfurl', help='CloudForms Appliance URL', required=True)
parser.add_argument('--cfuser', help='CloudForms Appliance User', required=True)
parser.add_argument('--cfpass', help='CloudForms Appliance Password', required=True)
parser.add_argument('--ufilter', help='User To Filter Searches To', required=True, default=None)
parser.add_argument('--session', help='Session', required=True, default=None)
parser.add_argument('--insecure', help='Use Insecure SSL Cert', action="store_false")
parser.add_argument('--labcode', help='Lab Code', required=True)
parser.add_argument('--group', help='Group Count for Batch Deletions', type=int, default=10)
parser.add_argument('--sleep', help='Sleep secs between groups', type=int, default=300)
args = parser.parse_args()

cfurl = args.cfurl
cfuser = args.cfuser
cfpass = args.cfpass
userFilter = args.ufilter
session = args.session
sslVerify = args.insecure
labCode = args.labcode
group = args.group
sleept = args.sleep

def gettok():
  response = requests.get(cfurl + "/api/auth", auth=HTTPBasicAuth(cfuser, cfpass), verify=sslVerify)
  data = response.json()
  return data['auth_token']

def apicall(token, url, op, inp = None ):
  #print("CFURL: " + cfurl)
  #print("URL: " + url)
  if url.startswith('http'):
    eurl = url
  else:
    eurl = cfurl + url
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(eurl, headers=head, verify=sslVerify)
  elif op == "post":
    response = requests.post(eurl, headers=head, verify=sslVerify, data = inp)
  #print("RESPONSE: " + response.text)
  obj = response.json()
  return obj.get('resources')

token = gettok()
surl = "/api/services?attributes=tags%2Ccustom_attributes&expand=resources"

if userFilter:
  url = "/api/users?expand=resources&filter%5B%5D=userid='" + userFilter + "'"
  #print("DEBUG: " + url)
  users = apicall(token, url, "get", inp = None )
  #print("DEBUG users: " + str(users))
  if not users:
    print(("ERROR: No such user " + userFilter))
    exit ()
  else:
    userID = str(users[0]['id'])
    surl = surl + "&filter%5B%5D=evm_owner_id='" + userID + "'"

services = apicall(token, surl, "get", inp = None )

svcURLs = []

for svc in services:
  lc = ""
  ses = ""
  for cab in svc['custom_attributes']:
    if cab['name'] == 'labCode':
      lc = cab['value']
    elif cab['name'] == 'session':
      ses = cab['value']
  if ses == session and lc == labCode:
    #print(svc['name'])
    #print(svc['href'])
    svcURLs.append(svc['href'])

PAYLOAD = '{ "action": "retire" }'

x = 0
print ("Queuing service retirements", end='', flush=True)
for svc in svcURLs:
  print('.', end='', flush=True)
  apicall(token, svc, "post", PAYLOAD)
  if x >= group:
    print('S', end='', flush=True)
    time.sleep(sleept)
    x = 0
  x = x + 1

print()
print()
