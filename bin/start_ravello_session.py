#!/usr/bin/python3

import argparse
import requests
import urllib.parse
import time
import ravello_sdk
from common import *

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
parser.add_argument('--ha', help='primary|secondary|none', default='primary', choices=['primary','secondary','none'])
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
ha = args.ha

def start(app,app_time,client):
        status = application_state(app)
        app_name = app['name'].encode('utf-8')
        if status == 'STARTED':
                print('Application {0} is in already in {1} state, no action needed'.format(app_name,status))
                exp = {'expirationFromNowSeconds': 60*app_time}
                client.set_application_expiration(app['id'], exp)
                print('Setting expiration time of application {0} to {1} minutes'.format(app_name,app_time))
        elif 'STARTING' in status or 'STOPPING' in status:
                print('Application {0} action in progress, not making any change'.format(app_name))
        elif 'STOPPED' in status:
                if app_time != 0:
                        exp = {'expirationFromNowSeconds': 60*app_time}
                        client.set_application_expiration(app['id'], exp)
                        print('Setting expiration time of application {0} to {1} minutes'.format(app_name,app_time))
                client.start_application(app['id'])
                print('Starting application {}'.format(app_name))
        else:
                log.error('Application {0} is in unknown state {1}, canceling START command'.format(app_name,status))
                print('Application {0} is in unknown state {1}, canceling START command'.format(app_name,status))
                return False
        return True

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

appIDs = []

for svc in services:
  lc = ""
  ses = ""
  appid = ""
  for cab in svc['custom_attributes']:
    if cab['name'] == 'labCode':
      lc = cab['value']
    elif cab['name'] == 'session':
      ses = cab['value']
    elif cab['name'] == 'applicationid':
      appid = cab['value']
    elif cab['name'] == 'HA':
      thisha = cab['value']
  if ha != "none":
    if ses == session and lc == labCode and thisha == ha:
      appIDs.append(appid)
  else:
    if ses == session and lc == labCode:
      #print(svc['name'])
      #print(svc['href'])
      appIDs.append(appid)

#Connect to Ravello
username,password = get_credentials()
client = connect(username, password)
if not client:
  exit (1)

x = 1
for appID in appIDs:
  app = client.get_application(appID)
  app_time = 480
  start(app,app_time,client)
  if x >= group:
    print('Sleeping')
    time.sleep(sleept)
    x = 0
  x = x + 1
