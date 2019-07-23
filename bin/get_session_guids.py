#!/usr/bin/python3

import csv
import os
import subprocess
import sys
import configparser, os
import re
from argparse import ArgumentParser

def mkparser():
  parser = ArgumentParser()
  parser.add_argument("--labcode", dest="labCode",default=None,help='Lab Code <lab code>',required=True)
  parser.add_argument("--profile", dest="profile",default=None,help='Profile <profile>',required=True)
  parser.add_argument("--session", dest="session",default=None,help='Session <session>')
  parser.add_argument("--ha", dest="ha",default=None,help='HA',choices=['primary','secondary'])
  return parser

def execute(command, quiet=False):
  process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if quiet:
    output = process.communicate()
    return
  while True:
    nextline = process.stdout.readline()
    if nextline == b'' and process.poll() is not None:
      break
    sys.stdout.write(nextline.decode('utf-8'))
    sys.stdout.flush()
  output = process.communicate()[0]
  exitCode = process.returncode
  if (exitCode == 0):
    return output
  else:
    prerror("ERROR: Command failed with return code (%s)" % exitCode)
    prerror("OUTPUT (%s)" % (output))

def prerror(msg):
  print ("%s" % msg )

parser = mkparser()
args = parser.parse_args()

labCode = args.labCode
profile = args.profile

if args.session:
  session = args.session
else:
  session = None

if args.ha:
  ha = args.ha
else:
  ha = None

ggroot = "/var/www/guidgrabber"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/bin/"
cfgfile = ggetc + "gg.cfg"
profileDir = ggetc + "/" + profile

labConfigCSV = profileDir + "/labconfig.csv"
if not os.path.exists(labConfigCSV):
  prerror("No lab config at %s" % labConfigCSV)
  exit(1)

allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
if os.path.exists(allGuidsCSV):
  os.remove(allGuidsCSV)

catName = ""
catItem = ""
environment = ""
shared = ""
blueprint = ""
infraWorkload = ""
studentWorkload = ""
envsize = ""
region = ""
regionBackup = ""
city = "unknown"
salesforce = "unknown"
surveyLink = ""
bareMetal = ""
serviceType = ""
spp = False
with open(labConfigCSV, encoding='utf-8') as csvFile:
  labcodes = csv.DictReader(csvFile)
  for row in labcodes:
    if row['code'] == labCode:
      catName = row['catname']
      catItem = row['catitem']
      environment = row['environment']
      if 'environment' in row and row['environment'] is not None and row['environment'] != "None" and environment == "spp":
        spp = True
      if 'blueprint' in row and row['blueprint'] is not None and row['blueprint'] != "None":
        blueprint = row['blueprint']
      if 'infraworkload' in row and row['infraworkload'] is not None and row['infraworkload'] != "None":
        infraWorkload = row['infraworkload']
      if 'studentworkload' in row and row['studentworkload'] is not None and row['studentworkload'] != "None":
        studentWorkload = row['studentworkload']
      if 'envsize' in row and row['envsize'] is not None and row['envsize'] != "None":
        envsize = row['envsize']
      if 'region' in row and row['region'] is not None and row['region'] != "None":
        region = row['region']
      if 'city' in row and row['city'] is not None and row['city'] != "None":
        city = row['city']
      if 'salesforce' in row and row['salesforce'] is not None and row['salesforce'] != "None":
        salesforce = row['salesforce']
      if 'surveylink' in row and row['surveylink'] is not None and row['surveylink'] != "None":
        surveyLink = row['surveylink']
      if 'baremetal' in row and row['baremetal'] is not None and row['baremetal'] != "None":
        bareMetal = row['baremetal']
      if 'servicetype' in row and row['servicetype'] is not None and row['servicetype'] != "None":
        serviceType = row['servicetype']
      if serviceType == "agnosticd-shared" or serviceType == "user-password":
        if 'shared' in row and row['shared'] is not None and row['shared'] != "None":
          shared = row['shared']
      break
if catName == "" or catItem == "":
  prerror("ERROR: Catalog item or name not set for lab code %s." % (labCode))
  exit(1)
if environment == "":
  prerror("ERROR: No environment set for lab code %s." % (labCode))
  exit(1)
elif environment == "rhpds":
  envirURL = "https://rhpds.redhat.com"
elif environment == "opentlc":
  envirURL = "https://labs.opentlc.com"
elif environment == "spp":
  envirURL = "https://spp.opentlc.com"
else:
  prerror("ERROR: Invalid environment %s." % (environment))
  exit(1)

config = configparser.ConfigParser()
config.read(cfgfile)
cfuser = config.get('cloudforms-credentials', 'user')
cfpass = config.get('cloudforms-credentials', 'password')

print ("Searching for GUIDs for lab code %s" % labCode )
getguids = ggbin + "getguids.py"
if shared != "" and shared != "None":
  command = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", "/dev/null", "--ufilter", profile, "--guidonly", "--labcode", labCode]
  if session is not None:
    command.extend(["--session", session])
  if ha is not None:
    command.extend(["--ha" , ha])
  #print(command)
  out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  if stdout != "" or stdout != "None":
    guid = stdout.rstrip().decode('ascii')
  if guid == "":
    print("ERROR: Could not find a deployed service in %s." % envirURL)
    exit()
  print ("Creating %s shared users..." % shared )
  with open(allGuidsCSV, "w", encoding='utf-8') as agc:
    ln = '"guid","appid","servicetype"\n'
    agc.write(ln)
    i = 1
    shr = int(shared)
    while i <= shr:
      user = str(i)
      ln = '"%s","%s","%s"\n' % (user, guid, "shared")
      i = i + 1
      agc.write(ln)
else:
  command = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allGuidsCSV, "--ufilter", profile, "--labcode", labCode]
  #print (command)
  if session is not None:
    command.extend(["--session", session])
  if ha is not None:
    command.extend(["--ha" , ha])
  execute(command)
