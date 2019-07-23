#!/usr/bin/python3

import argparse
import requests
#import urllib
import urllib.parse

import re
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(description="Get GUIDS From CloudForms")
parser.add_argument('--cfurl', help='CloudForms Appliance URL', required=True)
parser.add_argument('--cfuser', help='CloudForms Appliance User', required=True)
parser.add_argument('--cfpass', help='CloudForms Appliance Password', required=True)
parser.add_argument('--catalog', help='CloudForms Catalog The Item Is In', required=True)
parser.add_argument('--item', help='CloudForms Item Name', required=True)
parser.add_argument('--ufilter', help='User To Filter Searches To', required=False, default="")
parser.add_argument('--out', help='File to write CSV into', required=True)
parser.add_argument('--insecure', help='Use Insecure SSL Cert', action="store_false")
parser.add_argument('--guidonly', help='Return Only The GUID', action="store_true")
parser.add_argument('--shared', help='Number Of Shared Users (ONLY NON CF DEPLOYED!)', required=False, default=0)
parser.add_argument('--labcode', help='Lab Code (Optional)', required=False, default="")
parser.add_argument('--session', help='Session (Optional)', required=False, default="")
parser.add_argument('--ha', help='HA (Optional)', required=False, default=None, choices=['primary','secondary'])
args = parser.parse_args()

cfurl = args.cfurl
cfuser = args.cfuser
cfpass = args.cfpass
catName = args.catalog
catalogName = urllib.parse.quote(catName)
itName = args.item
itemName = urllib.parse.quote(itName)
userFilter = args.ufilter
outFile = args.out
shared = args.shared
sslVerify = args.insecure
guidOnly = args.guidonly
labCode = args.labcode
ha = args.ha
session = args.session

def gettok():
  response = requests.get(cfurl + "/api/auth", auth=HTTPBasicAuth(cfuser, cfpass), verify=sslVerify)
  data = response.json()
  return data['auth_token']

def apicall(token, url, op, inp = None ):
  #print("CFURL: " + cfurl)
  #print("URL: " + url)
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(cfurl + url, headers=head, verify=sslVerify)
    #print(response['resources']['count'])
  #print("RESPONSE: " + response.text)
  obj = response.json()
  return obj.get('resources')

f = open(outFile, 'w')
f.write("guid,appid,servicetype,sandboxzone\n")

if itName != "N/A" and itName != "None" and itName != "":
  token = gettok()

  url = "/api/service_catalogs?attributes=name,id&expand=resources&filter%5B%5D=name='" + catalogName + "'"
  cats = apicall(token, url, "get", inp = None )
  if not cats:
    print("ERROR: No such catalog " + catName)
    exit ()
  else:
    catalogID = str(cats[0]['id'])
    #print("Catalog ID: " + catalogID)

  url = "/api/service_templates?attributes=service_template_catalog_id,id,name&expand=resources&filter%5B%5D=name='" + itemName + "'&filter%5B%5D=service_template_catalog_id='" + catalogID + "'"
  items = apicall(token, url, "get", inp = None )
  #print "DEBUG: " + str(items)
  if not items:
    print(("ERROR: No such item " + itName))
    exit ()
  else:
    itemID = str(items[0]['id'])
    #print("Item ID: " + itemID)

  surl = "/api/services?attributes=tags%2Ccustom_attributes&expand=resources&limit=3000&filter%5B%5D=service_template_id='" + itemID + "'"

  if userFilter != "":
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

  if guidOnly:
    guid = ""
    lc = ""
    status = ""
    thissession = ""
    thisha = ""
    for svc in services:
      for cab in svc['custom_attributes']:
        if cab['name'] == 'GUID':
          guid = cab['value']
        if cab['name'] == 'labCode':
          lc = cab['value']
        if cab['name'] == 'service_status':
          status = cab['value']
        if cab['name'] == 'session':
          thissession = cab['value']
        if cab['name'] == 'HA':
          thisha = cab['value']
      if labCode:
        if guid != "" and lc == labCode and status == "complete":
          if session != "":
            if ha is not None:
              if thissession == session and thisha == ha:
                print(guid)
            else:
              if thissession == session:
                print(guid)
          else:
            print(guid)
          #exit ()
      elif guid != "" and status == "complete":
        print(guid)
        exit ()

  for svc in services:
    appID = ""
    guid = ""
    serviceType = ""
    lc = ""
    ln = ""
    sandboxZone = ""
    status = ""
    thisha = ""
    thissession = ""
    for cab in svc['custom_attributes']:
      if cab['name'] == 'GUID':
        guid = cab['value']
      elif cab['name'] == 'applicationid':
        appID = cab['value']
      elif cab['name'] == 'labCode':
        lc = cab['value']
      elif cab['name'] == 'service_status':
        status = cab['value']
      elif cab['name'] == 'sandboxzone':
        sandboxZone = cab['value']
      if cab['name'] == 'session':
        thissession = cab['value']
      if cab['name'] == 'HA':
        thisha = cab['value']
    if status != "complete":
      #print ("skipping")
      continue
    if guid != "":
      for tag in svc['tags']:
        if re.match(r'^\/managed\/servicetype', tag['name']):
          serviceType = re.split('/', tag['name'])[3]
          if serviceType == "ansible_deployer":
            serviceType = "agnosticd"
          break
    if labCode:
      #if labCode != lc:
      #  print("guid not found " + guid + " " + lc + " " + labCode)
      if labCode == lc:
        #print("found" + guid)
        if session != "":
          if ha is not None:
            #print("hacheck " + thissession + " " + session + " " + thisha + " " + ha)
            if thissession == session and thisha == ha:
              #print("writing " + thissession + " " + session + " " + thisha + " " + ha)
              ln=guid + "," + appID + "," + serviceType
          else:
            #print("reglcheck" + thissession + " " + session )
            if thissession == session:
              ln=guid + "," + appID + "," + serviceType
        else:
          ln=guid + "," + appID + "," + serviceType
    else:
      ln=guid + "," + appID + "," + serviceType
    if ln != "":
      if sandboxZone != "":
        ln = ln + "," + sandboxZone
      ln = ln + "\n"
      f.write(ln)
  #print ("Wrote file " + outFile)
else:
  i = 1
  shr = int(shared)
  while i <= shr:
    user = str(i)
    ln = '"%s","%s","%s"\n' % (user, "", "agnosticd-shared")
    i = i + 1
    f.write(ln)

f.close()
