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
  parser.add_argument("-l", dest="labCode",default=None,help='Lab Code <lab code>')
  parser.add_argument("-o", dest="operation",default=None,help='Operation <depoy_labs|delete_instances>')
  parser.add_argument("-p", dest="profile",default=None,help='Profile <profile>')
  parser.add_argument("-d", dest="deleteAssigned",default=None,help='Delete Assigned Guids')
  parser.add_argument("-n", dest="numInstances",default=None,help='Number of instances <num>')
  parser.add_argument("-s", dest="session",default=None,help='Session <session>')
  parser.add_argument("-g", dest="group",default="20",help='Deploy in Groups <num>')
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

if args.labCode is None:
  print ('-l <labcode> is required. See --help for usage.')
  exit (1)
else:
  labCode = args.labCode

if args.operation is None:
  print ('-o <depoy_labs|delete_instances> is required. See --help for usage.')
  exit (1)
else:
  operation = args.operation

if operation == "deploy_instances":
  if args.numInstances is None:
    print ('-n <num_instances> is required for deploy_instances. See --help for usage.')
    exit (1)
  else:
    num_instances = args.numInstances

if args.session:
  session = args.session

if args.group:
  group = args.group

if args.profile is None:
  print ('-p <profile> is required. See --help for usage.')
  exit (1)
else:
  profile = args.profile

if args.deleteAssigned is not None:
  deleteAssigned = True
else:
  deleteAssigned = False

ggroot = "/root/guidgrabber"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/bin/"
cfgfile = ggetc + "gg.cfg"
profileDir = ggetc + "/" + profile
labConfigCSV = profileDir + "/labconfig.csv"
allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"

if not os.path.exists(labConfigCSV):
  prerror("No lab config at %s" % labConfigCSV)
  exit(1)

#if not os.path.exists(allGuidsCSV):
#  prerror("No lab config at %s" % allGuidsCSV)
#  exit(1)

#if not os.path.exists(assignedCSV):
#  prerror("No lab config at %s" % assignedCSV)
#  exit(1)


if operation == "get_guids" or operation == "deploy_instances" or operation == "delete_instances":
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
  if operation == "get_guids":
    if serviceType == "user-password":
      prerror("User password type not supported.")
      exit(1)
    assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
    if deleteAssigned:
      if os.path.exists(assignedCSV):
        print ("Deleting assigned users...")
        os.remove(assignedCSV)
    if os.path.exists(allGuidsCSV):
      os.remove(allGuidsCSV)
    if shared != "" and shared != "None":
      print ("Searching for GUID for lab code %s" % labCode )
      getguids = ggbin + "getguids.py"
      config = configparser.ConfigParser()
      config.read(cfgfile)
      cfuser = config.get('cloudforms-credentials', 'user')
      cfpass = config.get('cloudforms-credentials', 'password')
      if spp:
        command = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", "/dev/null", "--ufilter", profile, "--guidonly", "--labcode", labCode]
      else:
        command = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", "/dev/null", "--ufilter", profile, "--labcode", labCode]
      out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      stdout,stderr = out.communicate()
      if stdout != "" or stdout != "None":
        guid = stdout.rstrip().decode('ascii')
      if guid == "":
        prerror("ERROR: Could not find a deployed service in %s." % envirURL)
        exit(1)
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
      print ("Please wait, getting GUIDs..." )
      getguids = ggbin + "getguids.py"
      config = configparser.ConfigParser()
      config.read(cfgfile)
      cfuser = config.get('cloudforms-credentials', 'user')
      cfpass = config.get('cloudforms-credentials', 'password')
      cmd = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allGuidsCSV, "--ufilter", profile]
      if spp:
        cmd.extend(["--labcode", labCode])
      #print(cmd)
      execute(cmd)
      if not os.path.exists(allGuidsCSV):
        prerror("ERROR: Updating GUIDs failed in environment %s." % (environment))
      else:
        num_lines = sum(1 for line in open(allGuidsCSV)) - 1
        if num_lines < 1:
          print ("We were able to find the catalog and catalog item, however it appears you do not have any services completely deployed in %s under your account %s.  If the services are still deploying you may need to try again later.  Also, make sure you didn't forget to deploy lab instances." % (environment, profile) )
        else:
          print ("Success! %s GUIDs defined for lab %s" % (str(num_lines), labCode) )
    exit()
  elif operation == "deploy_instances":
    config = configparser.ConfigParser()
    config.read(cfgfile)
    cfuser = config.get('cloudforms-credentials', 'user')
    cfpass = config.get('cloudforms-credentials', 'password')
    if not re.match("^[0-9]+$", num_instances):
      prerror("ERROR: Number of instances must be a valid number.")
      exit()
    if int(num_instances) < 1 or int(num_instances) > 55:
      prerror("ERROR: Number of instances must be a positive number.")
      exit()
    print ("Attempting to deploy %s instances of %s/%s in environment %s." % (num_instances, catName, catItem, environment) )
    ordersvc = ggbin + "order_svc.sh"
    settings = "check=t;expiration=7;runtime=8;labCode=%s;city=%s;salesforce=%s;notes=DeployedWithGuidGrabber" % (labCode, city, salesforce)
    if session:
      settings = settings + ";session=" + session
    if spp:
      if serviceType == "ravello":
        settings = 'autostart=f;noemail=t;pwauth=t;' + settings
        if blueprint != "":
          settings = '%s;blueprint=%s' % (settings, blueprint)
        if bareMetal != "":
          settings = '%s;bm=%s' % (settings, bareMetal)
      if serviceType == "agnosticd" or serviceType == "agnosticd-shared":
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
        region = "na_east"
        regionBackup = "eu_west"
        if bareMetal == "t":
          region = "na_west"
          regionBackup = "na_east"
      if serviceType == "agnosticd-shared":
        settings = '%s;region=%s_shared' % (settings, region)
      else:
        settings = '%s;region=%s' % (settings, region)
    cmd = [ordersvc, "-w", envirURL, "-u", profile, "-P", cfpass, "-c", catName, "-i", catItem, "-t", num_instances, "-n", "-d", settings]
    if regionBackup != "":
      cmd.extend(["-b", regionBackup])
    if serviceType == "ravello":
      cmd.extend([ "-g", group, "-p", "5" ])
    #print(cmd)
    execute(cmd)
    exit()
  elif operation == "delete_instances":
    print ("Attempting to delete all deployed instances of %s/%s in environment %s" % (catName, catItem, environment) )
    retiresvc = ggbin + "retire_svcs.sh"
    config = configparser.ConfigParser()
    config.read(cfgfile)
    cfuser = config.get('cloudforms-credentials', 'user')
    cfpass = config.get('cloudforms-credentials', 'password')
    cmd = [retiresvc, "-w", envirURL, "-u", cfuser, "-P", cfpass, "-f", profile, "-c", catName, "-i", catItem, "-n"]
    if serviceType == "ravello":
      cmd.extend([ "-g", "50", "-p", "5" ])
    if spp:
      cmd.extend([ "-l", labCode ])
    if session:
      cmd.extend([ "-s", session ])
    # DEBUG ONLY!
    #print (cmd)
    execute(cmd)
    print ("Retirement Queued." )
    if os.path.exists(assignedCSV):
      os.remove(assignedCSV)
    if os.path.exists(allGuidsCSV):
      os.remove(allGuidsCSV)
    exit()
  else:
    prerror("ERROR: Invalid Operation.")
    exit()
