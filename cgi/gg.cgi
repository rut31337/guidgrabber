#!/usr/bin/python

import csv
import cgi
import requests
import urllib
import Cookie
import datetime
import random
import os
import fcntl
import errno
from requests.auth import HTTPBasicAuth
from random import randint
import time
from time import sleep

def print_reset():
  print """
<script>
function rusure() {
    var txt;
    if (confirm("Warning: You should only do this if you just arrived to the lab session and are ready to begin or you are done with your lab entirely.  If you are sure click OK below otherwise, click Cancel.")) {
      window.location.href = "%s?profile=%s&operation=reset";
    }
}
</script>
""" % (myurl, profile)

def printback():
  print '<br><button onclick="goBack()">< Go Back</button>'

def callredirect(redirectURL, waittime=0):
  print '<head>'
  print '  <meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL)
  #print 'DEBUG:  redirect to ="%s;url=%s" />' % (waittime, redirectURL)
  print '</head><html><body></body></html>'

def includehtml(fname):
  with open(fname, 'r') as fin:
    print fin.read()

def printheader(redirect=False, redirectURL="", waittime="0", operation="requestguid", guid="", labCode="", appID=""):
  if operation == "reset":
      expiration = datetime.datetime.now()
      et = expiration.strftime("%a, %d-%b-%Y %H:%M:%S")
      c = Cookie.SimpleCookie()
      c["summitlabguid"] = ""
      c["summitlabguid"]["expires"] = et
      c["summitlabcode"] = ""
      c["summitlabcode"]["expires"] = et
      c["summitappid"] = ""
      c["summitappid"]["expires"] = et
      print c
  elif operation == "setguid":
    if guid != "":
      expiration = datetime.datetime.now() + datetime.timedelta(days=1)
      et = expiration.strftime("%a, %d-%b-%Y %H:%M:%S")
      c = Cookie.SimpleCookie()
      c["summitlabguid"] = guid
      c["summitlabguid"]["expires"] = et
      if labCode != "":
        c["summitlabcode"] = labCode
        c["summitlabcode"]["expires"] = et
      if appID != "":
        c["summitappid"] = appID
        c["summitappid"]["expires"] = et
      print c
  print "Content-type:text/html\r\n\r\n"
  if redirect and redirectURL != "":
    callredirect(redirectURL, waittime)
    exit()
  print '<html><head>'
  if operation == "showguid":
    includehtml('head.inc')
    print_reset()
  elif operation == "searchguid":
    includehtml('head3.inc')
  else:
    includehtml('head.inc')
  print '</head>'
  if operation == "showguid":
    includehtml('topbar2.inc')
    includehtml('textarea2.inc')
  elif operation == "searchguid":
    includehtml('topbar3.inc')
  else:
    includehtml('topbar.inc')
    includehtml('textarea.inc')

def printfooter(operation="requestguid"):
  if operation == "showguid":
    includehtml('footer2.inc')
  else:
    includehtml('footer.inc')
  print '</body>'
  print '</html>'
  exit()

def apicall(token, url, op, inp = None ):
  #print "<br>URL: " + op + "&nbsp;" + url + "<br>"
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(url, headers=head, verify=sslVerify)
  if op == "post":
    #print "<br>Payload: " + str(inp) + "<br>"
    response = requests.post(url, headers=head, json=inp, verify=sslVerify)
  if op == "put":
    #print "<br>Payload: " + str(inp) + "<br>"
    response = requests.put(url, headers=head, json=inp, verify=sslVerify)
  #print "<br>Response: (" + response.text + ")<br>"
  obj = response.json()
  if op == 'post':
    return obj.get('results')
  else:
    return obj.get('resources')

form = cgi.FieldStorage()
if 'profile' in form:
  profile = form.getvalue('profile')
else:
  printheader()
  print "ERROR: No profile specified."
  printfooter()
  exit()

myurl = "/gg/gg.cgi"
ggHtmlRoot = "/gg"
sslVerify = True
ggetc = "/var/www/guidgrabber/etc/"

profileDir = ggetc + "/" + profile
labConfigCSV = profileDir + "/labconfig.csv"

if not os.path.isfile(labConfigCSV):
  printheader()
  print "Sorry, labs for this session are not yet available.  Please try again later."
  printfooter()
  exit()

if 'operation' in form:
  operation = form.getvalue('operation')
else:
  operation = "requestguid"

if operation == "requestguid":
  if 'HTTP_COOKIE' in os.environ:
    cookie_string=os.environ.get('HTTP_COOKIE')
    c = Cookie.SimpleCookie()
    c.load(cookie_string)
    try:
      cguid = c['summitlabguid'].value
    except:
      cguid = ""
    try:
      clabCode = c['summitlabcode'].value
    except:
      clabCode = ""
    try:
      cappID = c['summitappid'].value
    except:
      cappID = ""
    if cguid != "" and clabCode != "":
      redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s" % (myurl,profile,cguid,clabCode,cappID)
      printheader(True, redirectURL, "0", operation)
      exit()
  foundlabs = False
  fl = {}
  with open(labConfigCSV) as csvFile:
    labCodes = csv.DictReader(csvFile)
    for row in labCodes:
      if row['code'].startswith("#"):
        continue
      assignedCSV = profileDir + "/availableguids-" + row['code'] + ".csv"
      if os.path.exists(assignedCSV):
        foundlabs = True
        fl[row['code']] = row['description']
  printheader()
  if not foundlabs:
    print "<tr><td><center><b>Sorry, the lab sessions are not yet available.</b></center></td></tr>"
  else:
    print "<center><table>"
    if 'msg' in form:
      print '<tr><td><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr><tr><td>&nbsp;</td></tr>"
    print '<tr><td><p style="color: black; font-size: 1.2em;">Please choose the lab code for this session (Reload this page if you do not see the option for this lab session in the below dropdown.):</p></td></tr>'
    print "<tr><td><form method='post' action='%s?operation=searchguid'>" % myurl
    print "<table border=0><tr><td><b>Lab Code:</b></td><td><select name='labcode'>"
    for k in fl:
      print('<option value="{0}">{0} - {1}</option>'.format(k,fl[k]))
    print "</select></td></tr>"
    print "<tr><td><b>Activation Key:</b></td><td><input type='text' name='actkey'></td></tr>"
    print '<tr><td colspan=2 align=center><input type="submit" value="Next&nbsp;>"></td></tr></table>'
    print '<input type="hidden" id="ipaddr" name="ipaddr" />'
    print '<input type="hidden" id="profile" name="profile" value="%s" />' % profile
  print "</form></td></tr>"
  if foundlabs:
    print '<tr><td><p style="color: black; font-size: 0.9em;">If you are unsure which one to choose or what the activation key is please notify a lab proctor.</p><br></td></tr>'
  print '</table></center>'
  if foundlabs:
    print '<script type="text/javascript" src="' + ggHtmlRoot + '/ipgrabber.js"></script>'
  printfooter(operation)
elif operation == "reset":
  redirectURL=myurl + "?profile=" + profile
  printheader(True, redirectURL, "0", operation)
  exit()
elif operation == "searchguid":
  printheader(operation = operation)
  if 'actkey' not in form:
    print "ERROR, no activation key provided."
    printback()
    printfooter()
    exit ()
  actkey = form.getvalue('actkey')
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
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  if not os.path.exists(assignedCSV):
    with open(assignedCSV, "a") as ipfile:
      ipfile.write("guid,ipaddr\n")
  if 'ipaddr' not in form:
    print "ERROR, no ipaddr provided."
    printback()
    printfooter()
    exit ()
  ipaddr = form.getvalue('ipaddr')
  if actkey == 'loadtest':
    activated = True
  else:
    activated = False
    with open(labConfigCSV) as csvFile:
      labCodes = csv.DictReader(csvFile)
      for row in labCodes:
        if row['code'] == labCode:
            if actkey == row['activationkey']:
              activated = True
  if activated == False:
    msg=urllib.quote("ERROR, The activation key you entered does not match for lab code <b>{0}</b>, please contact a lab proctor if you feel this is an error.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  foundGuid = ""
  appID = ""
  with open(assignedCSV) as ipfile:
    iplocks = csv.DictReader(ipfile)
    for row in iplocks:
      if row['ipaddr'] == ipaddr:
        foundGuid = row['guid']
        break
  if foundGuid != "":
    with open(allGuidsCSV) as allfile:
      allf = csv.DictReader(allfile)
      for allrow in allf:
        if allrow['guid'] == foundGuid:
          appID = allrow['appid']
          break
  if foundGuid != "":
    redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s" % (myurl,profile,foundGuid,labCode,appID)
    printheader(True, redirectURL, "0", operation)
    exit()
  assignedGuid = False
  #sleep(randint(1,5))
  allGuids = {}
  with open(allGuidsCSV) as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      allGuids[allrow['guid']] = True
  ipfile = open(assignedCSV)
  while True:
    try:
      fcntl.flock(ipfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
      break
    except IOError as e:
      # raise on unrelated IOErrors
      if e.errno != errno.EAGAIN:
        raise
      else:
        time.sleep(0.1)
  foundGuid = ""
  iplocks = csv.DictReader(ipfile)
  usedGuids = {}
  for row in iplocks:
    usedGuids[row['guid']] = True
  for g in allGuids:
    if g not in usedGuids:
      foundGuid = g
      break
  if foundGuid != "":
    ipfile = open(assignedCSV, 'a')
    ipfile.write(foundGuid + "," + ipaddr + "\n")
    assignedGuid = True
    with open(allGuidsCSV) as allfile:
      allf = csv.DictReader(allfile)
      for allrow in allf:
        if allrow['guid'] == foundGuid:
          appID = allrow['appid']
          break
  fcntl.flock(ipfile, fcntl.LOCK_UN)
  if not assignedGuid:
    msg=urllib.quote("Sorry, there are no available GUIDs for lab <b>{0}</b>, please double check that you selected the correct lab code or contact a lab proctor.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  else:
    redirectURL="%s?profile=%s&operation=setguid&guid=%s&labcode=%s&appid=%s" % (myurl,profile,foundGuid,labCode,appID)
    printheader(True, redirectURL, "0")
    exit()
elif operation == "setguid":
  if 'labcode' not in form:
    printheader()
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit ()
  labCode = form.getvalue('labcode')
  if 'guid' not in form:
    printheader()
    print "ERROR, no guid provided."
    printback()
    printfooter()
    exit ()
  foundGuid = form.getvalue('guid')
  #if 'appid' not in form:
  #  printheader()
  #  print "ERROR, no appid provided."
  #  printback()
  #  printfooter()
  #  exit ()
  if 'appid' in form:
    appID = form.getvalue('appid')
  else:
    appID = ""
  redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s" % (myurl,profile,foundGuid,labCode,appID)
  printheader(True, redirectURL, "0", operation, foundGuid, labCode, appID)
  exit()
elif operation == "showguid":
  if 'labcode' not in form:
    printheader()
    print "Unexpected ERROR: no labcode forwarded. Please contact lab proctor."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  bastion = ""
  docURL = ""
  description = ""
  urls = ""
  labUser = ""
  labSSHkey = ""
  found = False
  with open(labConfigCSV) as csvFile:
    labCodes = csv.DictReader(csvFile)
    for row in labCodes:
      if row['code'] == labCode:
        found = True
        bastion = row['bastion']
        docURL = row['docurl']
        description = row['description']
        urls = row['urls']
        labUser = row['labuser']
        labSSHkey = row['labsshkey']
        break
  printheader(False, "", "", operation)
  if not found:
    print "Unexpected ERROR: This lab no longer exists. Please contact lab proctor.<br>"
    print "Only if <b>directed by lab proctor</b> click this button: <button onclick='rusure()'>RESET STATION</button>"
    printback()
    printfooter()
    exit()
  if 'guid' not in form:
    print "Unexpected ERROR: no GUID found. Please contact lab proctor."
    printback()
    printfooter()
    exit()
  guid = form.getvalue('guid')
  print "<center><table border=0>"
  print "<tr><td>"
  print "<center><h2>Welcome to: %s</h2><h3>Your assigned lab GUID is:</h3><table border=1><tr><td align=center><font size='7'><pre>%s</pre></font></td></tr></table></center>" % (description,guid)
  print "Let's get started! Please read these instructions carefully before starting to have the best lab experience:"
  print "<ul><li>Save the above <b>GUID</b> as you will need it to access your lab's systems from your workstation.</li>"
  if docURL != "" and docURL != "None":
    docURL = docURL.replace('REPL', guid)
    print "<li>Open the lab guide by clicking <a href='%s' target='_blank'>here</a></li>" % docURL
  print "<li>Consult the lab guide instructions <i>before</i> attempting to connect to the lab environment.</li>"
  if labSSHkey != "" and labSSHkey != "None":
    print "<li>You can download the lab SSH key from <a href='%s'>here</a>.</li>" % labSSHkey
    print "<li>Save this key (example filename: keyfile.pem) then run <pre>chmod 0600 keyfile.pem</pre></li>"
  if bastion != "" and bastion != "None":
    bastion = bastion.replace('REPL', guid)
    if labUser != "":
      print "<li>The generic SSH login for this lab is <b>%s</b></li>" % labUser
      lu = "%s@" % labUser
    else:
      lu = ""
    if labSSHkey != "" and labSSHkey != "None":
      lk = "-i /path/to/keyfile.pem "
    else:
      lk = ""
    print "<li>When prompted to do so by the lab instructions, you can SSH to your bastion host by opening a terminal and issuing the following command:<br><pre>[lab-user@localhost ~]$ ssh %s%s%s</pre></li>" % (lk, lu, bastion)
  else:
    #if urls != "None":
    #  print ("<li>For example, if the lab requires you to access a URL it would be like this<br><pre>https://host-{0}.rhpds.opentlc.com</pre></li>".format(guid))
    if bastion != "" and bastion != "None":
      print ("<li>If lab requires the use of the SSH command it would look like this:<br><pre>ssh host-{0}.rhpds.opentlc.com</pre></li>".format(guid))
    #print "<li><b>Note:</b>These are <b>just examples</b>, please consult the lab instructions for actual host names and URLs.</li>"
  if urls != "" and urls != "None":
    print "<li>The following URLs will be used in your lab environment. Please only access these links when the lab instructions specify to do so:<ul>"
    for u in urls.split(";"):
      u = u.replace('REPL', guid)
      if u.startswith("*"):
        print ("<li>Wildcard DNS entry: <b>{0}</b></li>".format(u))
      else:
        print ("<li><a href='{0}' target='_blank'>{0}</a></li>".format(u))
    print "<li>Note: The lab guide may specify other host names and/or URLs.</li>"
    print "</ul>"
  if bastion == "None" and urls == "None":
    print "<li>Please consult the lab guide for any host names and/or URLs that you may need to connect to.</li>"
  if 'appid' in form:
    appid = form.getvalue('appid')
    print "<li>You can access your detailed lab environment information at <a href='https://www.opentlc.com/summit-status/status.php?appid=%s&guid=%s' target='_blank'>here</a></li>" % (appid,guid)
    consoleURL="https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid,appid)
    print "<li>If <b>required</b> by the lab guide instructions, you can reach your environment's power control and consoles by clicking: <a href='%s' target='_blank'>here</a></li>" % consoleURL
  print "<li>To clear the way for the next attendee, please click the below <b>RESET STATION</b> button when you are <i>completely finished</i> with your lab.</li>"
  print "</ul></td></tr></table>"
  print "<p>If the current lab session is <b>just starting</b> or you are <b>completely finished with your current lab</b> please click the button below to reset this station.</p>"
  print "<button onclick='rusure()'>RESET STATION</button>"
  print "</center>"
  printfooter(operation)
else:
  printheader()
  print "Unexpected ERROR: invalid operation. Please contact lab proctor."
  printfooter()
