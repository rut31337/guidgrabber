#!/usr/bin/python3

import argparse
import requests
import urllib.parse

import re
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(description="Get GUIDS From CloudForms")
parser.add_argument('--cfurl', help='CloudForms Appliance URL', required=True)
parser.add_argument('--cfuser', help='CloudForms Appliance User', required=True)
parser.add_argument('--cfpass', help='CloudForms Appliance Password', required=True)
parser.add_argument('--ufilter', help='User To Filter Searches To', required=False, default="")
parser.add_argument('--insecure', help='Use Insecure SSL Cert', action="store_false")
parser.add_argument('--labcode', help='Lab Code (Optional)', required=False, default="")
args = parser.parse_args()

cfurl = args.cfurl
cfuser = args.cfuser
cfpass = args.cfpass
userFilter = args.ufilter
sslVerify = args.insecure
labCode = args.labcode

print("<center><table border=1 style='border-collapse: collapse;'>")
print("<tr><th colspan=4>Service Build Status For Lab %s:</th></tr>" % labCode)
print("<tr><th>GUID</th><th>Status</th><th>Sandbox Zone</th><th>Kube Admin</th></tr>")

def gettok():
  response = requests.get(cfurl + "/api/auth", auth=HTTPBasicAuth(cfuser, cfpass), verify=sslVerify)
  data = response.json()
  return data['auth_token']

def apicall(token, url, op, inp = None ):
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(cfurl + url, headers=head, verify=sslVerify)
  obj = response.json()
  return obj.get('resources')

token = gettok()
surl = "/api/services?attributes=tags%2Ccustom_attributes&expand=resources&limit=3000"
if userFilter != "":
  url = "/api/users?expand=resources&filter%5B%5D=userid='" + userFilter + "'"
  users = apicall(token, url, "get", inp = None )
  if not users:
    print(("ERROR: No such user " + userFilter))
    exit ()
  else:
    userID = str(users[0]['id'])
    surl = surl + "&filter%5B%5D=evm_owner_id='" + userID + "'"
services = apicall(token, surl, "get", inp = None )
for svc in services:
  guid = ""
  status = ""
  sandboxZone = ""
  kubeadmin = ""
  lc = ""
  for cab in svc['custom_attributes']:
    if cab['name'] == 'GUID':
      guid = cab['value']
    elif cab['name'] == 'labCode':
      lc = cab['value']
    elif cab['name'] == 'service_status':
      status = cab['value']
    elif cab['name'] == 'sandboxzone':
      sandboxZone = cab['value']
    elif cab['name'] == 'kubeadmin':
      kubeadmin = cab['value']
  if labCode:
    if labCode != lc:
      continue
  if guid == "":
    guid = "unknown"
  if status == "":
    status = "incomplete"
  print ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (guid, status, sandboxZone, kubeadmin) )

print ("</table><br>")
