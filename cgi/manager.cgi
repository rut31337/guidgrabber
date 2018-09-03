#!/usr/bin/python

import csv
import cgi
import urllib
import os
import subprocess
import sys
import ConfigParser, os
import re
import datetime

def manageApp(client, op, app, runTime=0):
  status = application_state(app)
  if op == "start":
    ate = 3600*runTime
    exp = {'expirationFromNowSeconds': ate}
    if status == 'STARTED' or 'STARTING' in status:
      print "App %s is in state %s, extending runtime by %s hours.<br>" % (str(app['id']), status, str(runTime))
      client.set_application_expiration(app['id'], exp)
    elif 'STOPPED' in status:
      if runTime != 0:
        client.set_application_expiration(app['id'], exp)
      print "Starting appID %s with runtime of %s hours.<br>" % (str(app['id']), str(runTime))
      client.start_application(app['id'])
    elif 'STOPPING' in status:
      print "No action possible, appID %s, is in state %s.<br>" % (str(app['id']), status)
      return True
    else:
      print "Warning: appID %s is in an unhandled state of %s.<br>" % (str(app['id']), status)
  elif op == "stop":
    if 'STARTED' in status:
      print "Stopping appID %s.<br>" % (str(app['id']))
      client.stop_application(app['id'])
    elif 'STOPPED' in status:
      print "appID %s is already stopped.<br>" % (str(app['id']))
    elif 'STARTING' in status or 'STOPPING' in status:
      print "No action for appID %s, it is in transient state %s.<br>" % (str(app['id']), status)
      return True
    else:
      print "Warning: appID %s is in an unhandled state of %s.<br>" % (str(app['id']), status)

def execute(command, quiet=False):
  process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if quiet:
    output = process.communicate()
    return
  while True:
    nextline = process.stdout.readline()
    if nextline == '' and process.poll() is not None:
      break
    sys.stdout.write(nextline)
    sys.stdout.flush()
  output = process.communicate()[0]
  exitCode = process.returncode
  if (exitCode == 0):
    return output
  else:
    prerror("ERROR: Command failed with return code (%s)<br>OUT(%s)" % (exitCode, output))

def prerror(msg):
  print "<center>%s<br></center>" % msg

def printback():
  print '<button class="w3-btn w3-white w3-border w3-padding-small" onclick="goBack()"><&nbsp;Back</button>'

def printback2():
  print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s'\" type=button><&nbsp;Back</button>" % myurl

def printback3(labCode):
  print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s'\" type=button><&nbsp;Back</button>" % (myurl, labCode)

def callredirect(redirectURL, waittime=0):
  print '<head>'
  print '<meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL)
  print '</head><html><body></body></html>'

def includehtml(fname):
  with open(fname, 'r') as fin:
    print fin.read()

def printheader(redirect=False, redirectURL="", waittime="0", operation="none"):
  print "Content-type:text/html\r\n\r\n"
  if redirect and redirectURL != "":
    callredirect(redirectURL, waittime)
    exit()
  print '<html><head>'
  includehtml('head_mgr.inc')
  print '</head>'
  includehtml('topbar.inc')
  includehtml('textarea_mgr.inc')

def printfooter(operation="none"):
  if operation is not "mainmenu":
    print '<center><button class="w3-btn w3-white w3-border w3-padding-small" onclick="window.location.href=\'/gg/manager.cgi\'">Home</button></center>'
  includehtml('footer2.inc')
  print '</body>'
  print '</html>'
  exit()

def printform(operation="", labcode="", labname="", labkey="", bastion="", docurl="", laburls="", catname="", catitem="", labuser="", labsshkey="", environment="", blueprint="", shared=""):
  print "<center><table>"
  if operation == 'create_lab':
    print '<tr><td colspan=2 align=center><p style="color: black; font-size: 0.6em;">There are no labs set up for your user <b>' + profile + '</b> please fill out this form to create one:</p></td></tr>'
  print '<tr><td><form method="post" action="%s?operation=%s">' % (myurl, operation)
  print "<table border=0>"
  if operation == 'update_lab':
    print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Code*:</b></td><td><input type='hidden' name='labcode' size='20' value='%s'>%s</td></tr>" % (labcode, labcode)
  else:
    print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Code (Alphanumeric Only)*:</b></td><td><input type='text' name='labcode' size='20'></td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Name*:</b></td><td><input type='text' name='labname' size='80' value='%s'></td></tr>" %  labname
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Key*:</b></td><td><input type='text' name='labkey' size='20' value='%s'></td></tr>" % labkey
  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><b>NOTE:</b> For all fields specifying FQDN or URL you can use the string <b>REPL</b> which will be replaced by GUID (ex. bastion-REPL.rhpds.opentlc.com)</td></tr>"
  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><hr></td></tr>"
  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><b>NOTE:</b> Catalog and item names must match exactly with what is in CloudForms!</td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Catalog Name*:</b></td><td><input type='text' name='catname' size='20' value='%s'></td></tr>" % catname
  print "<tr><td align=right style='font-size: 0.6em;'><b>Catalog Item*:</b></td><td><input type='text' name='catitem' size='20' value='%s'></td></tr>" % catitem
  opc = ""
  rhc = ""
  spp = ""
  if environment == "opentlc":
    opc = "checked"
  elif environment == "rhpds":
    rhc = "checked"
  elif environment == "spp":
    spp = "checked"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Environment*:</b></td><td style='font-size: 0.6em;'>"
  print "<input type='radio' name='environment' value='rhpds' " + rhc + ">RHPDS"
  print "<input type='radio' name='environment' value='opentlc' " + opc + ">OPENTLC"
  print "<input type='radio' name='environment' value='spp' " + spp + ">SPP"
  print "</td></tr>"

  print "<tr><td align=right style='font-size: 0.6em;'><b>Shared User Count (AAD Shared Only):</b></td><td><input type='text' name='shared' size='80' value='%s'></td></tr>" % shared 

  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><hr></td></tr>"
  print "<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about SSH in your GUID page</td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Bastion FQDN:</b></td><td><input type='text' name='bastion' size='40' value='%s'></td></tr>" % bastion
  print "<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about SSH keys.</td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab SSH Key URL:</b></td><td><input type='text' name='labsshkey' size='80' value='%s'></td></tr>" % labsshkey
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab User Login:</b></td><td><input type='text' name='labuser' size='80' value='%s'></td></tr>" % labuser
  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><hr></td></tr>"
  print "<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about URLs in your GUID page</td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Semicolon Delimited List of Lab URLs (ex. https://www-REPL.rhpds.opentlc.com):</b></td><td><textarea cols='80' name='laburls'>%s</textarea></td></tr>" % laburls
  print "<tr><td align=center style='font-size: 0.6em;' colspan=2><hr></td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Documentation URL:</b></td><td><input type='text' name='docurl' size='80' value='%s'></td></tr>" % docurl
  print "<tr><td align=right style='font-size: 0.6em;'></td><td><input type='hidden' name='blueprint' size='80' value='%s'></td></tr>" % blueprint
  print '<tr><td colspan=2 align=center>'
  printback2()
  print '<input class="w3-btn w3-white w3-border w3-padding-small" type="submit" value="Next&nbsp;>"></td></tr></table>'
  print "</form></td></tr>"
  print '</table></center>'

if not os.environ.get('REMOTE_USER'): 
  printheader()
  prerror("ERROR: No profile specified.")
  printfooter()
  exit()
else:
  profile = os.environ.get('REMOTE_USER')

myurl = "/gg/manager.cgi"
ggurl = "https://www.opentlc.com/gg/gg.cgi"
ggroot = "/var/www/guidgrabber"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/bin/"
cfgfile = ggetc + "gg.cfg"

profileDir = ggetc + "/" + profile
if not os.path.isdir(profileDir):
  os.mkdir(profileDir)
labConfigCSV = profileDir + "/labconfig.csv"
labCSVheader = "code,description,activationkey,bastion,docurl,urls,catname,catitem,labuser,labsshkey,environment,blueprint,shared\n"

form = cgi.FieldStorage()
if 'operation' in form:
  operation = form.getvalue('operation')
else:
  operation = "none"
if operation == "none":
  if not os.path.exists(labConfigCSV):
    printheader()
    printform('create_lab')
    printfooter()
    exit()
  printheader()
  print "<center><table>"
  if 'msg' in form:
    print '<tr><td><p style="color: black; font-size: .7em;">' + form.getvalue('msg') + "</p></td></tr>"
  #<tr><td>&nbsp;</td></tr>"
  print "<tr><td style='font-size: .7em;' colspan=2>Choose an operation <b>%s</b>:</td></tr>" % profile
  print "<tr><td style='font-size: .7em;'><a href=%s?operation=create_new_lab_form>Add A New Lab Configuration</a></td></tr>" % myurl
  found = False
  with open(labConfigCSV) as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      else:
        found = True
        break
  if os.path.exists(labConfigCSV) and found:
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=edit_lab>View/Edit Lab Configuration</a></td></tr>" % myurl
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=deploy_lab>Deploy Lab Instances</a></td></tr>" % myurl
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=update_guids>Update Available Lab GUIDs</a></td></tr>" % myurl
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=choose_lab>Manage Lab</a></td></tr>" % myurl
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=delete_instance>Delete Lab Instances</a></td></tr>" % myurl
    print "<tr><td style='font-size: .7em;'><a href=%s?operation=delete_lab>Delete Lab Configuration</a></td></tr>" % myurl
    print "<tr><td colspan=2>&nbsp;</td></tr><tr><td style='font-size: .6em;' colspan=2>Share this link with your attendees:<br><b>%s?profile=%s</b><br>TIP: Use bit.ly or similar tool to shorten link.</td></tr>" % (ggurl, profile)
  print '</table></center>'
  printfooter("mainmenu")
  exit()
elif operation == "create_new_lab_form":
  printheader()
  printform('create_new_lab')
  printfooter()
  exit()
elif operation == "choose_lab" or operation == "edit_lab" or operation == "delete_lab" or operation == "update_guids" or operation == "deploy_lab" or operation == "delete_instance":
  printheader()
  print "<center><table border=0>"
  if 'msg' in form:
    print '<tr><td><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr>"
  if operation == "choose_lab":
    op = "<b>view</b>"
    op2 = "checklc"
  elif operation == "delete_lab":
    op = "<b>delete <font color=red>(Danger, unrecoverable operation!)</font></b>"
    op2 = "dellc"
  elif operation == 'edit_lab':
    op = "<b>view/edit</b>"
    op2 = "editlc"
  elif operation == 'update_guids':
    op = "<b>delete and update available GUIDs for</b>"
    op2 = "get_guids"
  elif operation == 'deploy_lab':
    op = "<b>deploy instances for</b>"
    op2 = "deploy_labs"
  elif operation == 'delete_instance':
    op = "<b>delete instances for <font color=red>(Danger, unrecoverable operation!)</font></b>"
    op2 = "delete_instances"
  else:
    prerror("ERROR: Unknown operation.")
    printfooter()
    exit()
  print '<form method="post" action="%s?operation=%s">' % (myurl, op2)
  print '<tr><td colspan=2 align=center><p style="color: black; font-size: .8em;">Please choose the lab you wish to %s:</p></td></tr>' % op
  print "<tr><td colspan=2 align=center style='font-size: .6em;'><select name='labcode'>"
  with open(labConfigCSV) as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      print('<option value="{0}">{0} - {1}</option>'.format(row['code'],row['description']))
  print "</select></td></tr>"
  if operation == 'deploy_lab':
    print "<tr><td align=right style='font-size: 0.6em;'><b>Number Of Instances To Deploy:</b></td><td><input type='text' name='num_instances' size='2'></td></tr>"
  if operation == 'deploy_lab' or operation == 'delete_instance':
    print "<tr><td align=right style='font-size: 0.6em;'><b>Password for user %s:</b></td><td><input type='password' name='cfpass' size='8'></td></tr>" % (profile)
  print '<tr><td colspan=2 align=center>'
  printback2()
  print '<input class="w3-btn w3-white w3-border w3-padding-small" type="submit" value="Next&nbsp;>"></td></tr>'
  print '</form></table></center>'
  printfooter(operation)
  exit()
elif operation == "create_lab" or operation == 'create_new_lab':
  if 'labcode' not in form or 'labname' not in form or 'labkey' not in form or 'catname' not in form or 'catitem' not in form:
    printheader()
    prerror("ERROR: Please fill out required fields.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  if not (re.match("^[a-zA-Z0-9]+$", labCode)):
    printheader()
    prerror("ERROR: Lab code any only be alphanumeric.")
    printback()
    printfooter()
    exit()
  if not os.path.exists(labConfigCSV):
    with open(labConfigCSV, "w") as conffile:
      conffile.write(labCSVheader)
  else:
    with open(labConfigCSV) as conffile:
      labcodes = csv.DictReader(conffile)
      for row in labcodes:
        if row['code'] == labCode:
          printheader()
          prerror("ERROR: Lab %s already defined.  Delete it first.<br><center>" % (labCode))
          printback2()
          printfooter()
          exit()
  labName = form.getvalue('labname')
  labKey = form.getvalue('labkey')
  bastion = form.getvalue('bastion')
  docURL = form.getvalue('docurl')
  labURLs = form.getvalue('laburls')
  catName = form.getvalue('catname')
  catItem = form.getvalue('catitem')
  labUser = form.getvalue('labuser')
  labSSHkey = form.getvalue('labsshkey')
  environment = form.getvalue('environment')
  shared = form.getvalue('shared')
  blueprint = form.getvalue('blueprint')
  ln = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (labCode, labName, labKey, bastion, docURL, labURLs, catName, catItem, labUser, labSSHkey, environment, blueprint, shared)
  with open(labConfigCSV, "a") as conffile:
    conffile.write(ln)
  ms="Lab <b>%s - %s</b> Has Been Created<ul style='color: black; font-size: .7em;'><li>Please copy this link: <b>%s?profile=%s</b></li><li>You should create a short URL for this link and provide it to your users.</li><li>Next step is to use <b>Deploy Lab Instances</b> below.</li></ul>" % (labCode, labName, ggurl, profile)
  msg=urllib.quote(ms)
  redirectURL="%s?msg=%s" % (myurl, msg)
  printheader(True, redirectURL, "0", "none")
  exit()
elif operation == "checklc" or operation == "dellc" or operation == "editlc":
  if 'labcode' not in form:
    printheader()
    prerror("ERROR: No labcode provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  valid = False
  with open(labConfigCSV) as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'] == labCode:
        valid = True
        break
  if valid == False:
    printheader()
    prerror("ERROR: The lab code provided not match a valid lab code.")
    printback()
    printfooter()
    exit()
  if operation == "checklc":
    op = "view_lab"
  elif operation == "dellc":
    op = "del_lab"
  elif operation == "editlc":
    op = "print_lab"
  redirectURL = "%s?operation=%s&labcode=%s" % (myurl, op, labCode)
  printheader(True, redirectURL, "0")
  printfooter()
  exit()
elif operation == "print_lab":
  if 'labcode' not in form:
    printheader()
    prerror("ERROR: No labcode provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  with open(labConfigCSV) as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'] == labCode:
        if 'shared' not in row:
          row['shared'] = ""
        printheader()
        printform('update_lab', row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], row['blueprint'], row['shared'])
        printfooter()
        exit()
  printheader()
  prerror("ERROR: Labcode %s not found.<br><center>" % (labCode))
  printfooter()
  exit()
elif operation == "power_on" or operation == "power_off":
  printheader()
  if 'labcode' not in form:
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit ()
  labCode = form.getvalue('labcode')
  allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
  if not os.path.exists(allGuidsCSV):
    msg=urllib.quote("ERROR, No guids for lab code <b>{0}</b> exist.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  config = ConfigParser.ConfigParser()
  config.read(cfgfile)
  ravUser = config.get('ravello-credentials', 'user')
  ravPw = config.get('ravello-credentials', 'password')
  from ravello_sdk import *
  client = RavelloClient()
  try:
    client.login(ravUser, ravPw)
  except:
    prerror('Error: Unable to connect to Ravello or invalid user credentials')
  with open(allGuidsCSV) as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      if 'servicetype' in allrow and allrow['servicetype'] == "ravello":
        appID = allrow['appid']
        try:
	  app = client.get_application(appID)
        except:
          prerror('Strange appid %s not found.' % (str(appID)))
          continue
        if operation == "power_on":
          if 'runtime' in form:
            runTime = int(form.getvalue('runtime'))
          else: 
            runTime = 8
          manageApp(client, "start", app, runTime)
        elif operation == "power_off":
          manageApp(client, "stop", app, 0)
  printback()
  printfooter()
  exit()
elif operation == "view_lab" or operation == "del_lab" or operation == "update_lab":
  if 'labcode' not in form:
    printheader()
    prerror("ERROR: No labcode provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  if operation == "del_lab" or operation == "update_lab":
    f = open(labConfigCSV)
    old = f.readlines()
    f.close()
    with open(labConfigCSV, "w") as conffile:
      conffile.write(labCSVheader)
    f = open(labConfigCSV,"a")
    labcodes = csv.DictReader(old)
    if operation == "del_lab":
      for row in labcodes:
        if row['code'] != labCode:
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], row['blueprint'], row['shared'])
          f.write(out)
      if os.path.exists(allGuidsCSV):
        os.remove(allGuidsCSV)
      if os.path.exists(assignedCSV):
        os.remove(assignedCSV)
    elif operation == "update_lab":
      for row in labcodes:
        if row['code'] == labCode:
          labName = form.getvalue('labname')
          labKey = form.getvalue('labkey')
          catName = form.getvalue('catname')
          catItem = form.getvalue('catitem')
          bastion = form.getvalue('bastion')
          docURL = form.getvalue('docurl')
          labURLs = form.getvalue('laburls')
          labUser = form.getvalue('labuser')
          labSSHkey = form.getvalue('labsshkey')
          environment = form.getvalue('environment')
          blueprint = form.getvalue('blueprint')
          shared = form.getvalue('shared')
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (labCode, labName, labKey, bastion, docURL, labURLs, catName, catItem, labUser, labSSHkey, environment, blueprint, shared)
        else:
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], row['blueprint'], row['shared'])
        f.write(out)
    f.close()
    redirectURL = "%s?operation=none" % (myurl)
    printheader(True, redirectURL, "0")
    printfooter()
    exit()
  asg = 0
  tot = 0
  rowc = 0
  maxrow = 10
  ravello = False
  if not os.path.exists(allGuidsCSV):
    msg=urllib.quote("ERROR: No guids for lab code <b>{0}</b> exist.<br><center>".format(labCode))
    redirectURL="%s?msg=%s" % (myurl, msg)
    printheader(True, redirectURL, "0", operation)
    printfooter()
    exit()
  printheader()
  print "<center><b>Lab %s<b><table border=1 style='border-collapse: collapse;'>" % labCode
  ravello = False
  with open(allGuidsCSV) as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      if 'servicetype' in allrow and allrow['servicetype'] == 'ravello':
        ravello = True
  if ravello:
    config = ConfigParser.ConfigParser()
    config.read(cfgfile)
    ravUser = config.get('ravello-credentials', 'user')
    ravPw = config.get('ravello-credentials', 'password')
    from ravello_sdk import *
    client = RavelloClient()
    try:
      client.login(ravUser, ravPw)
    except:
      prerror('Error: Unable to connect to Ravello or invalid user credentials')
  with open(allGuidsCSV) as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      status = ""
      runTime = ""
      tot = tot + 1
      if rowc == 0:
        print "<tr>"
      print "<td>"
      print "<table border=0>"
      guid = allrow['guid']
      serviceType = ""
      if 'servicetype' in allrow:
        serviceType = allrow['servicetype']
      print "<tr><td style='font-size: 0.6em;' align=center><a href='%s?operation=manage_guid&guid=%s&labcode=%s'>%s</b></td></tr>" % (myurl, guid, labCode, guid)
      if serviceType == "ravello":
        appID = allrow['appid']
        try:
          app = client.get_application(appID)
        except:
          prerror('Strange appid %s not found.' % (str(appID)))
        try:
          status = application_state(app)
          if app['published']:
            deployment = app['deployment']
            if deployment['totalActiveVms'] > 0:
              if not deployment.has_key('expirationTime'):
                runTime = "Never"
              else:
                expirationTime = datetime.datetime.utcfromtimestamp(deployment['expirationTime'] / 1e3)
                delta = expirationTime - datetime.datetime.utcnow()
                (h,m) = str(delta).split(':')[:2]
                runTime = "%s:%s" % (h, m)
          ravurl = "https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid, appID)
          print "<tr><td style='font-size: 0.6em;'><a href='%s' target='_blank'>Lab Dashboard</a></td></tr>" % ravurl
        except:
          status = "ERROR: Non-Existant"
      assigned = False
      locked = False
      if os.path.exists(assignedCSV):
        with open(assignedCSV) as ipfile:
          iplocks = csv.DictReader(ipfile)
          for row in iplocks:
            if row['guid'] == guid:
              foundGuid = row['guid']
              assigned = True
              asg = asg + 1
              ipaddr = row['ipaddr']
              if ipaddr == "locked":
                locked = True
              #print '<tr><td><a href="vnc://%s">Remote Desktop</a></td></tr>' % ipaddr
              break
      if assigned and not locked:
        print "<tr><td align=center style='font-size: 0.6em; color: green;'>Assigned</td></tr>"
      elif locked:
        print "<tr><td align=center style='font-size: 0.6em; color: red;'>Locked</td></tr>"
      else:
        print "<tr><td align=center style='font-size: 0.6em; color: red;'>Not Assigned</td></tr>"
      if status != "":
        if status == "STARTED":
          color = "green"
        elif status == "STOPPED" or status == "ERROR: Non-Existant":
          color = "red"
        else:
          color = "gray"
        print "<tr><td align=center style='font-size: 0.6em; color: %s;'>%s</td></tr>" % (color, status)
      if runTime != "":
        print "<tr><td align=center style='font-size: 0.6em;'>Time Left: %s</td></tr>" % (runTime)
      print "</table>"
      print "</td>"
      rowc = rowc + 1
      if rowc == maxrow:
        print "</tr>"
        rowc = 0
  print "</table>"
  print "<table border=0>"
  print "<tr><th style='font-size: 0.6em;'>Total Labs:</th><td style='font-size: 0.6em;'>%s</td>" % tot
  print "<th style='font-size: 0.6em;'>Assigned Labs:</th><td style='font-size: 0.6em;'>%s</td>" % asg
  avl = tot - asg
  print "<th style='font-size: 0.6em;'>Available Labs:</th><td style='font-size: 0.6em;'>%s</td></tr>" % avl
  print "<tr><td colspan=6 align=center>"
  if ravello:
    print """
<script>
function pwrOnWarn() {
    var runtime = prompt("Enter new runtime (in hours) and click OK.", "8");
    if (runtime == null || runtime == "") {
      txt = "Cancelled";
    } else {
      window.location.href = "%s?profile=%s&operation=power_on&labcode=%s&runtime=" + runtime;
    }
}
</script>
""" % (myurl, profile, labCode)
    print """
<script>
function pwrOffWarn() {
    var txt;
    if (confirm("DANGER: Are you sure you wish to immediately power OFF all of your instances?  If you are sure click OK below otherwise, click Cancel.")) {
      window.location.href = "%s?profile=%s&operation=power_off&labcode=%s";
    }
}
</script>
""" % (myurl, profile, labCode)
    print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick='pwrOnWarn()'>Power ON All Instances/Extend Runtime</button>"
    print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick='pwrOffWarn()'>Power OFF All Instances</button>"
    print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=get_guids&labcode=%s'\" type=button>Update Available Lab GUIDs</button>" % (myurl, labCode)
  print "</td></tr>"
  print "<tr><td colspan=6 align=center>"
  printback2()
  print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"history.go(0)\" type=button>Refresh</button></td></tr>"
  print "</table></center>"
  printfooter(operation)
  exit()
elif operation == "get_guids" or operation == "deploy_labs" or operation == "delete_instances":
  if 'labcode' not in form:
    printheader()
    prerror("ERROR: No labcode provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
  catName = ""
  catItem = ""
  environment = ""
  shared = ""
  #labuser = "lab-user"
  with open(labConfigCSV) as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'] == labCode:
        catName = row['catname']
        catItem = row['catitem']
        environment = row['environment']
        #if row['labuser'] != "" and row['labuser'] != "None":
        #  labuser = row['labuser']
        if 'shared' in row and row['shared'] != "None":
          shared = row['shared']
        break
  if catName == "" or catItem == "":
    printheader()
    prerror("ERROR: Catalog item or name not set for lab code %s." % (labCode))
    printback()
    printfooter()
    exit()
  if environment == "":
    printheader()
    prerror("ERROR: No environment set for lab code %s." % (labCode))
    printback()
    printfooter()
    exit()
  elif environment == "rhpds":
    envirURL = "https://rhpds.redhat.com"
  elif environment == "opentlc":
    envirURL = "https://labs.opentlc.com"
  elif environment == "spp":
    envirURL = "https://spp.opentlc.com"
  else:
    printheader()
    prerror("ERROR: Invalid environment %s." % (environment))
    printback()
    printfooter()
    exit()
  if operation == "get_guids":
    printheader()
    if os.path.exists(allGuidsCSV):
      os.remove(allGuidsCSV)
    if shared != "" and shared != "None":
      print "<center>Creating %s shared users..." % shared
      getguids = ggbin + "getguids.py"
      config = ConfigParser.ConfigParser()
      config.read(cfgfile)
      cfuser = config.get('cloudforms-credentials', 'user')
      cfpass = config.get('cloudforms-credentials', 'password')
      command = [getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", "/dev/null", "--ufilter", profile, "--guidonly"]
      out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      stdout,stderr = out.communicate()
      if stdout != "" or stdout != "None":
        guid = stdout.rstrip()
      else:
        prerror("ERROR: Could not find a deployed service.")
        printback()
        printfooter()
        exit()
      with open(allGuidsCSV, "w") as agc:
        ln = '"guid","appid","servicetype"\n'
        agc.write(ln)
        i = 1
        shr = int(shared)
        while i <= shr:
          #user = labuser + str(i)
          user = str(i)
          ln = '"%s","%s","%s"\n' % (user, guid, "shared")
          i = i + 1
          agc.write(ln)
      print "<br><button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s'\" type=button>View Lab&nbsp;></button>" % (myurl, labCode)
    else:
      print "<center>Please wait, looking for GUIDs..."
      print "<pre>"
      getguids = ggbin + "getguids.py"
      config = ConfigParser.ConfigParser()
      config.read(cfgfile)
      cfuser = config.get('cloudforms-credentials', 'user')
      cfpass = config.get('cloudforms-credentials', 'password')
      execute([getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allGuidsCSV, "--ufilter", profile])
      print "</pre>"
      if not os.path.exists(allGuidsCSV):
        prerror("ERROR: Updating GUIDs failed in environment <b>%s</b>." % (environment))
      else:
        num_lines = sum(1 for line in open(allGuidsCSV)) - 1
        if num_lines < 1:
          print "We were able to find the catalog and catalog item, however it appears you do not have any services deployed in <b>%s</b> under your account <b>%s</b>.  Did you forget to deploy lab instances?" % (environment, profile)
        else:
          print "Success! <b>%s</b> GUIDs defined for lab <b>%s</b><br>" % (str(num_lines), labCode)
          printback2()
          print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s'\" type=button>View Lab&nbsp;></button>" % (myurl, labCode)
      print "</center>"
    printfooter()
    exit()
  elif operation == "deploy_labs":
    if 'num_instances' not in form:
      printheader()
      prerror("ERROR: No number of instances provided.")
      printback()
      printfooter()
      exit()
    num_instances = form.getvalue('num_instances')
    if 'cfpass' not in form:
      printheader()
      prerror("ERROR: CloudForms password not provided.")
      printback()
      printfooter()
      exit()
    cfpass = form.getvalue('cfpass')
    if not re.match("^[0-9]+$", num_instances):
      printheader()
      prerror("ERROR: Number of instances must be a number <= 50.")
      printback()
      printfooter()
      exit()
    if int(num_instances) < 1 or int(num_instances) > 50 and profile != "rhtemgr":
      printheader()
      prerror("ERROR: Number of instances must be a number <= 50.")
      printback()
      printfooter()
      exit()
    printheader()
    print "Attempting to deploy <b>%s</b> instances of <b>%s/%s</b> in environment <b>%s</b>.<br><pre>" % (num_instances, catName, catItem, environment)
    ordersvc = ggbin + "order_svc.sh"
    execute([ordersvc, "-w", envirURL, "-u", profile, "-P", cfpass, "-c", catName, "-i", catItem, "-t", num_instances, "-n", "-d", "check=t;autostart=t;noemail=t"])
    print "</pre><center>"
    print "If deployment started successfully, wait at least 20 minutes from the output of this message (to complete deployment and GUID generation) then click <a href=%s?operation=update_guids>here</a> to update available the available GUIDs database.  Optionally you can use <b>Update Available Lab GUIDs</b> from the main menu.<br><center>" % myurl
    printfooter()
    exit()
  elif operation == "delete_instances":
    if 'cfpass' not in form:
      printheader()
      prerror("ERROR: CloudForms password not provided.")
      printback()
      printfooter()
      exit()
    cfpass = form.getvalue('cfpass')
    printheader()
    print "Attempting to delete all deployed instances of <b>%s/%s</b> in environment <b>%s</b>.<br><pre>" % (catName, catItem, environment)
    retiresvc = ggbin + "retire_svcs.sh"
    execute([retiresvc, "-w", envirURL, "-u", profile, "-P", cfpass, "-c", catName, "-i", catItem, "-n"])
    print "</pre><center>Retirement Queued.<br>"
    printback2()
    print "<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=dellc&labcode=%s'\" type=button>Delete Lab Configuration&nbsp;></button>" % (myurl, labCode)
    print "</center>"
    printfooter()
    exit()
  else:
    printheader()
    prerror("ERROR: Invalid Operation.")
    printback()
    printfooter()
    exit()
elif operation == "manage_guid":
  if 'labcode' not in form or 'guid' not in form:
    printheader()
    prerror("ERROR: No labcode and/or guid provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  guid = form.getvalue('guid')
  locked = False
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  if os.path.exists(assignedCSV):
    with open(assignedCSV) as ipfile:
      iplocks = csv.DictReader(ipfile)
      for row in iplocks:
        if row['guid'] == guid:
          ipaddr = row['ipaddr']
          if ipaddr == "locked":
            locked = True
          break
  printheader()
  print "<center><table>"
  print "<tr><td style='font-size: .6em;' colspan=2>Choose a operation for GUID <b>%s</b>, <b>%s</b>:</td></tr>" % (guid, profile)
  if not locked:
    print "<tr><td style='font-size: .6em;'><a href=%s?operation=lock_guid&guid=%s&labcode=%s>Lock GUID Availability</a> - Remove GUID from available pool. This will release current user (if any) as well!</td></tr>" % (myurl, guid, labCode)
  print "<tr><td style='font-size: .6em;'><a href=%s?operation=release_guid&guid=%s&labcode=%s>Release GUID</a> - Make GUID generally available even if already in use <font color=red>(Danger!)</font></td></tr>" % (myurl, guid, labCode)
  print "<tr><td colspan=2 align=center>"
  printback3(labCode)
  print '</td></tr>'
  print '</table></center>'
  printfooter()
  exit()
elif operation == "lock_guid" or operation == "release_guid":
  if 'labcode' not in form or 'guid' not in form:
    printheader()
    prerror("ERROR: No labcode and/or guid provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  guid = form.getvalue('guid')
  printheader()
  if os.path.exists(assignedCSV):
    regex = '/%s/d' % guid
    execute(["/bin/sed", "-i", regex, assignedCSV], quiet=True)
  if operation == "lock_guid":
    if not os.path.exists(assignedCSV):
      ln = '"guid","ipaddr"\n'
      with open(assignedCSV, "w") as conffile:
        conffile.write(ln)
    ln = '"%s","locked"\n' % (guid)
    with open(assignedCSV, "a") as conffile:
      conffile.write(ln)
  print "<center>"
  if operation == "lock_guid":
    print "GUID <b>%s</b> Locked<br>" % guid
  elif operation == "release_guid":
    print "GUID <b>%s</b> Released<br>" % guid
  print "Remember: If a user was assigned this GUID, make sure they use the <b>Reset Station</b> button to obtain a new GUID!<br>"
  printback3(labCode)
  print "</center>"
  printfooter()
  exit()
else:
  printheader()
  prerror("ERROR: Invalid operation.")
  printback()
  printfooter()
  exit()
