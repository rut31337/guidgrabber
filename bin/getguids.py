#!/usr/bin/python

import argparse
import requests
import urllib
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(description="Get GUIDS From CloudForms")
parser.add_argument('--cfurl', help='CloudForms Appliance URL', required=True)
parser.add_argument('--cfuser', help='CloudForms Appliance User', required=True)
parser.add_argument('--cfpass', help='CloudForms Appliance Password', required=True)
parser.add_argument('--catalog', help='CloudForms Catalog The Item Is In', required=True)
parser.add_argument('--item', help='CloudForms Item Name', required=True)
parser.add_argument('--out', help='File to write CSV into', required=True)
parser.add_argument('--insecure', help='Use Insecure SSL Cert', action="store_false")
args = parser.parse_args()

cfurl = args.cfurl
cfuser = args.cfuser
cfpass = args.cfpass
catName = args.catalog
catalogName = urllib.quote(catName)
itName = args.item
itemName = urllib.quote(itName)
outFile = args.out
sslVerify = args.insecure

def gettok():
  response = requests.get(cfurl + "/api/auth", auth=HTTPBasicAuth(cfuser, cfpass), verify=sslVerify)
  data = response.json()
  return data['auth_token']

def apicall(token, url, op, inp = None ):
  #print "URL: " + url
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(cfurl + url, headers=head, verify=sslVerify)
  #print "RESPONSE: " + response.text
  obj = response.json()
  return obj.get('resources')

token = gettok()

url = "/api/service_catalogs?attributes=name,id&expand=resources&filter%5B%5D=name%3D" + catalogName
cats = apicall(token, url, "get", inp = None )
if not cats:
  print "ERROR: No such catalog " + catName
  exit ()
else:
  catalogID = str(cats[0]['id'])
  #print "Catalog ID: " + catalogID

url = "/api/service_templates?attributes=service_template_catalog_id,id,name&expand=resources&filter%5B%5D=name=" + itemName + "&filter%5B%5D=service_template_catalog_id%3D" + catalogID
items = apicall(token, url, "get", inp = None )
if not items:
  print "ERROR: No such item " + itName
  exit ()
else:
  itemID = str(items[0]['id'])
  #print "Item ID: " + itemID

url = "/api/services?attributes=href%2Ctags%2Cname%2Ccustom_attributes%2Coptions&expand=resources&filter%5B%5D=service_template_id%3D" + itemID
services = apicall(token, url, "get", inp = None )

f = open(outFile, 'w')
f.write("guid,appid\n")

for svc in services:
  appID = ""
  guid = ""
  for cab in svc['custom_attributes']:
    if cab['name'] == 'GUID':
      guid = cab['value']
    elif cab['name'] == 'applicationid':
      appID = cab['value']
  f.write(guid + "," + appID + "\n")

f.close()
