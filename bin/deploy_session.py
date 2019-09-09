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
  parser.add_argument("-l", dest="labCode",default=None,help='Lab Code <lab code>',required=True)
  parser.add_argument("-p", dest="profile",default=None,help='Profile <profile>',required=True)
  parser.add_argument("-n", dest="numInstances",default=None,help='Number of instances <num>',required=True)
  parser.add_argument("-s", dest="session",default=None,help='Session <session>')
  parser.add_argument("-S", dest="sleep",default="5",help='Sleep <sleep>')
  parser.add_argument("-r", dest="region",default=None,help='Region <region>')
  parser.add_argument("-g", dest="group",default="20",help='Deploy in Groups <num>')
  parser.add_argument("-c", dest="cfgfile",default="event-deploy.cfg",help='Config File <cfg>')
  parser.add_argument("-D", dest="debug", action="store_true")
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
num_instances = args.numInstances
if args.session:
  session = args.session
group = args.group
profile = args.profile

if args.region:
  regionOverride = args.region
else:
  regionOverride = ""

ggroot = "/root/provision"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/common/"

cfgfile = ggetc + args.cfgfile
profileDir = ggetc + "/" + profile

labConfigCSV = profileDir + "/labconfig.csv"
if not os.path.exists(labConfigCSV):
  prerror("No lab config at %s" % labConfigCSV)
  exit(1)

slp = args.sleep

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
        if regionOverride != "":
          region = row['region']
        else:
          region = regionOverride
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
cfuser = config.get(profile, 'user')
cfpass = config.get(profile, 'password')
if not re.match("^[0-9]+$", num_instances):
  prerror("ERROR: Number of instances must be a valid number.")
  exit()
if int(num_instances) < 1:
  prerror("ERROR: Number of instances must be a positive number.")
  exit()
print ("Attempting to deploy %s instances of %s/%s in environment %s." % (num_instances, catName, catItem, environment) )
ordersvc = ggbin + "order_svc.sh"
settings = "check=t;check2=t;expiration=7;runtime=8;labCode=%s;city=%s;salesforce=%s;notes=DeployedWithGuidGrabber" % (labCode, city, salesforce)
if session:
  settings = settings + ";session=" + session
if spp:
  if serviceType == "ravello":
    settings = 'autostart=f;noemail=t;pwauth=t;' + settings
    if blueprint != "":
      settings = '%s;blueprint=%s' % (settings, blueprint)
    if bareMetal != "":
      settings = '%s;bm=%s' % (settings, bareMetal)
  if serviceType == "agnosticd" or serviceType == "agnosticd-shared" or serviceType == "agnosticd-nosandbox":
    if infraWorkload != "":
      settings = '%s;infra_workloads=%s' % (settings, infraWorkload)
    if studentWorkload != "":
      settings = '%s;student_workloads=%s' % (settings, studentWorkload)
    if envsize != "":
      settings = '%s;envsize=%s' % (settings, envsize)
    settings = settings + ';users=1'
  if serviceType == "agnosticd-shared":
    if shared != "":
      settings = '%s;users=%s' % (settings, shared)
if region != "":
  if serviceType == "ravello":
    if bareMetal == "t":
      region = region + "_baremetal"
    elif bareMetal == "g":
      region = region + "_gce"
    settings = '%s;region=%s' % (settings, region)
  elif serviceType == "agnosticd-shared" or serviceType == "agnosticd-nosandbox":
    settings = '%s;region=%s' % (settings, region)
  elif serviceType == "agnosticd":
    settings = '%s;region=%s_sandboxes_gpte' % (settings, region)
  else:
    settings = '%s;region=%s' % (settings, region)
cmd = [ordersvc, "-w", envirURL, "-u", profile, "-P", cfpass, "-c", catName, "-i", catItem, "-t", num_instances, "-n", "-d", settings]
if regionBackup != "":
  cmd.extend(["-b", regionBackup])
cmd.extend([ "-g", group, "-p", slp ])
if args.debug:
  print(cmd)
else:
  execute(cmd)
exit()
