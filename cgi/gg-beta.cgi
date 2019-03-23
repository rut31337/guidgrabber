#!/usr/bin/python3

import csv
import cgi
import requests
import urllib.request, urllib.parse, urllib.error
import http.cookies
import datetime
import random
import os
import fcntl
import errno
from requests.auth import HTTPBasicAuth
from random import randint
import time
from time import sleep

# WARNING: This is very insecure to set to True.  Set this to True only if you want to 
# enable a default activation key of 'loadtest' for load testing purposes.  
loadTestActive = False
#loadTestActive = True

def print_reset():
  print(("""
<script>
function rusure() {
    var txt;
    if (confirm("Warning: You should only do this if you just arrived to the lab session and are ready to begin or you are done with your lab entirely.  If you are sure click OK below otherwise, click Cancel.")) {
      window.location.href = "%s?profile=%s&operation=reset";
    }
}
</script>
""" % (myurl, profile)))

def printback():
  print('<br><button onclick="goBack()">< Go Back</button>')

def callredirect(redirectURL, waittime=0):
  print('<head>')
  print(('  <meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL)))
  #print('DEBUG:  redirect to ="%s;url=%s" />' % (waittime, redirectURL))
  print('</head><html><body></body></html>')

def includehtml(fname):
  with open(fname, 'r', encoding='utf-8') as fin:
    print((fin.read()))

def printheader(redirect=False, redirectURL="", waittime="0", operation="requestguid", guid="", labCode="", appID="", sandboxZone=""):
  if operation == "reset":
      expiration = datetime.datetime.now()
      et = expiration.strftime("%a, %d-%b-%Y %H:%M:%S")
      c = http.cookies.SimpleCookie()
      c["summitlabguid"] = ""
      c["summitlabguid"]["expires"] = et
      c["summitlabcode"] = ""
      c["summitlabcode"]["expires"] = et
      c["summitappid"] = ""
      c["summitappid"]["expires"] = et
      c["sandboxzone"] = ""
      c["sandboxzone"]["expires"] = et
      print(c)
  elif operation == "setguid":
    if guid != "":
      expiration = datetime.datetime.now() + datetime.timedelta(hours=2)
      et = expiration.strftime("%a, %d-%b-%Y %H:%M:%S")
      c = http.cookies.SimpleCookie()
      c["summitlabguid"] = guid
      c["summitlabguid"]["expires"] = et
      if labCode != "":
        c["summitlabcode"] = labCode
        c["summitlabcode"]["expires"] = et
      if appID != "":
        c["summitappid"] = appID
        c["summitappid"]["expires"] = et
      if sandboxZone != "":
        c["sandboxzone"] = sandboxZone
        c["sandboxzone"]["expires"] = et
      print(c)
  print("Content-type:text/html\r\n\r\n")
  if redirect and redirectURL != "":
    callredirect(redirectURL, waittime)
    exit()
  print('<html><head>')
  print("""
<script>
var isSafari = window.safari !== undefined;

if (isSafari) {
    alert("We are sorry but, unfortunately, Safari is not compatible with our application.");
}

if (/Edge/.test(navigator.userAgent)) {
    alert("We are sorry but, unfortunately, Microsoft browsers are not compatible with our application.");
}

</script>
""")
  if operation == "showguid":
    includehtml('head.inc')
    print_reset()
  elif operation == "searchguid":
    includehtml('head3.inc')
  else:
    includehtml('head.inc')
  print('</head>')
  if operation == "showguid":
    if "summit" in profile or profile == "generic_tester":
      includehtml('topbar2-summit.inc')
    elif profile == "generic_sko":
      includehtml('topbar2-sko.inc')
    else:
      includehtml('topbar2.inc')
    includehtml('textarea2.inc')
  elif operation == "searchguid":
    includehtml('topbar3.inc')
  else:
    if "summit" in profile or profile == "generic_tester":
      includehtml('topbar-summit.inc')
    elif profile == "generic_sko":
      includehtml('topbar-sko.inc')
    else:
      includehtml('topbar.inc')
    includehtml('textarea.inc')

def printfooter(operation="requestguid"):
  if operation == "showguid":
    includehtml('footer.inc')
  else:
    includehtml('footer.inc')
  print('</body>')
  print('</html>')
  exit()

def apicall(token, url, op, inp = None ):
  #print("<br>URL: " + op + "&nbsp;" + url + "<br>")
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2'}
  if op == "get":
    response = requests.get(url, headers=head, verify=sslVerify)
  if op == "post":
    #print("<br>Payload: " + str(inp) + "<br>")
    response = requests.post(url, headers=head, json=inp, verify=sslVerify)
  if op == "put":
    #print("<br>Payload: " + str(inp) + "<br>")
    response = requests.put(url, headers=head, json=inp, verify=sslVerify)
  #print("<br>Response: (" + response.text + ")<br>")
  obj = response.json()
  if op == 'post':
    return obj.get('results')
  else:
    return obj.get('resources')

form = cgi.FieldStorage()
if 'profile' in form:
  profile = form.getvalue('profile')
else:
  profile = ""
  printheader()
  print("ERROR: No profile specified.  Please check for typing errors or get the correct URL from a lab assistant.")
  printfooter()
  exit()

myurl = "/gg/gg-beta.cgi"
ggHtmlRoot = "/gg"
sslVerify = True
ggetc = "/var/www/guidgrabber/etc/"

profileDir = ggetc + "/" + profile
labConfigCSV = profileDir + "/labconfig.csv"

if not os.path.isfile(labConfigCSV):
  printheader()
  print("Lab environments for this session are not yet available.")
  printfooter()
  exit()

if 'operation' in form:
  operation = form.getvalue('operation')
else:
  operation = "requestguid"

if operation == "requestguid":
  if 'HTTP_COOKIE' in os.environ:
    cookie_string=os.environ.get('HTTP_COOKIE')
    c = http.cookies.SimpleCookie()
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
    try:
      csandboxZone = c['sandboxzone'].value
    except:
      csandboxZone = ""
    if cguid != "" and clabCode != "":
      redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s&sandboxzone=%s" % (myurl,profile,cguid,clabCode,cappID,csandboxZone)
      printheader(True, redirectURL, "0", operation)
      exit()
  foundlabs = False
  fl = {}
  with open(labConfigCSV, encoding='utf-8') as csvFile:
    labCodes = csv.DictReader(csvFile)
    for row in labCodes:
      if row['code'].startswith("#"):
        continue
      assignedCSV = profileDir + "/availableguids-" + row['code'] + ".csv"
      if os.path.exists(assignedCSV):
        foundlabs = True
        fl[row['code']] = row['description']
  printheader()
  print('<script language="JavaScript" src="' + ggHtmlRoot + '/gen_validatorv4.js" type="text/javascript" xml:space="preserve"></script>')
  print("<center><table width=60% border=0>")
  if profile == "generic_tester":
    print("<tr><td colspan=2><center><p style='color: purple;'>*** THIS IS THE UAT ENVIRONMENT - FOR TESTING ONLY ***</p></center></td></tr>")
  if not foundlabs:
    print("<tr><td colspan=2><center><b>The lab environments are not yet available.</b></center></td></tr>")
  else:
    if 'msg' in form:
      print(('<tr><td colspan=2><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr><tr><td>&nbsp;</td></tr>"))
    print("<form id='requestAccess' name='requestAccess' method='post' action='%s?operation=searchguid'>" % myurl)
    print("<tr><th style='color: black; font-size: .9em;' width=30% align=right>Lab Code:</th><td width=80%><select name='labcode'>")
    for k in sorted(fl):
      print(('<option value="{0}">{0} - {1}</option>'.format(k,fl[k])))
    print("</select></td></tr>")
    print("<tr><th style='color: black; font-size: .9em;' width=30% align=right>Activation Key:</th><td width=80%><div id='requestAccess_actkey_errorloc' class='error_strings'></div><input type='text' name='actkey'></td></tr>")
    print("<tr><th style='color: black; font-size: .9em;' width=30% align=right>E-Mail Address:</th><td width=80%><div id='requestAccess_email1_errorloc' class='error_strings'></div><input type='text' name='email1'></td></tr>")
    print("<tr><th style='color: black; font-size: .9em;' width=30% align=right>E-Mail Address:</th><td width=80%><div id='requestAccess_email2_errorloc' class='error_strings'></div><input type='text' name='email2'></td></tr>")
    print('<tr><td colspan=2><ul>')
    print('<li><div style="color: black; font-size: .9em;">Please choose the lab code for this session, enter the activation key, and your e-mail address then click <b>Submit</b>.</div></li>')
    print('<li><div style="color: black; font-size: .9em;">You may need to refresh this page if you do not see an option for this lab session in the dropdown.</div></li>')
    print('<li><div style="color: black; font-size: .9em;">If you are unsure which lab code to choose or what the activation key is please notify a lab assistant.</div></li>')
    print('<li><div style="color: black; font-size: .9em;">All fields are <b>required</b>. Red Hat will <b>not</b> store or share the entered e-mail address after this session is over or <i>ever</i> e-mail you, this is for tracking of this session only.</div></li>')
    print('</ul></td></tr>')
    print('<tr><td colspan=2 align=center><input class="w3-btn w3-white w3-border w3-padding-small" type="submit" value="Submit&nbsp;"></td></tr>')
    print('<input type="hidden" id="ipaddr" name="ipaddr" />')
    print(('<input type="hidden" id="profile" name="profile" value="%s" />' % profile))
    print("</form>")
    print("""
<script language="JavaScript" type="text/javascript"
    xml:space="preserve">
function DoCustomValidation()
{
  var frm = document.forms["requestAccess"];
  if(frm.email1.value != frm.email2.value)
  {
    sfm_show_error_msg('The E-Mail addresses do not match!',frm.email1);
    return false;
  }
  else
  {
    return true;
  }
}
//<![CDATA[
    var frmvalidator  = new Validator("requestAccess");
    frmvalidator.EnableOnPageErrorDisplay();
    frmvalidator.EnableMsgsTogether();
    frmvalidator.addValidation("email1","maxlen=50");
    frmvalidator.addValidation("email1","email","Enter Valid E-Mail Address");
    frmvalidator.addValidation("email1","req","Required Field");
    frmvalidator.addValidation("email2","maxlen=50");
    frmvalidator.addValidation("email2","email","Enter Valid E-Mail Address");
    frmvalidator.addValidation("email2","req","Required Field");
    frmvalidator.addValidation("actkey","req","Required Field");
    frmvalidator.setAddnlValidationFunction(DoCustomValidation);
// ]]>
</script>
""")
  if profile == "generic_tester":
    print("<tr><td colspan=2><center><p style='color: purple;'>*** THIS IS THE UAT ENVIRONMENT - FOR TESTING ONLY ***</p></center></td></tr>")
  print('</table></center>')
  if foundlabs:
    print(('<script type="text/javascript" src="' + ggHtmlRoot + '/ipgrabber.js"></script>'))
  printfooter(operation)
elif operation == "reset":
  redirectURL=myurl + "?profile=" + profile
  printheader(True, redirectURL, "0", operation)
  exit()
elif operation == "searchguid":
  printheader(operation = operation)
  if 'actkey' not in form:
    print("ERROR, no activation key provided.")
    printback()
    printfooter()
    exit ()
  actkey = form.getvalue('actkey')
  if 'labcode' not in form:
    print("ERROR, no labcode provided.")
    printback()
    printfooter()
    exit ()
  labCode = form.getvalue('labcode')
  allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
  if not os.path.exists(allGuidsCSV):
    msg=urllib.parse.quote("ERROR, No guids for lab code <b>{0}</b> exist.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  if not os.path.exists(assignedCSV):
    with open(assignedCSV, "a", encoding='utf-8') as ipfile:
      ipfile.write("guid,ipaddr,email\n")
  if 'ipaddr' not in form:
    print("ERROR, no ipaddr provided.")
    printback()
    printfooter()
    exit ()
  ipaddr = form.getvalue('ipaddr')
  if 'email1' not in form:
    print("ERROR, no E-mail provided.")
    printback()
    printfooter()
    exit ()
  email1 = form.getvalue('email1')
  if 'email2' not in form:
    print("ERROR, no E-mail provided.")
    printback()
    printfooter()
    exit ()
  email2 = form.getvalue('email2')
  if email1 != email2:
    print("ERROR, E-mail addresses do not match.")
    printback()
    printfooter()
    exit ()
  email = email1
  if actkey == 'loadtest' and loadTestActive:
    activated = True
  else:
    activated = False
    with open(labConfigCSV, encoding='utf-8') as csvFile:
      labCodes = csv.DictReader(csvFile)
      for row in labCodes:
        if row['code'] == labCode:
            if actkey == row['activationkey']:
              activated = True
  if activated == False:
    msg=urllib.parse.quote("ERROR, The activation key you entered does not match for lab code <b>{0}</b>, please contact a lab assistant if you feel this is an error.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  foundGuid = ""
  appID = ""
  sandboxZone = ""
  with open(assignedCSV, encoding='utf-8') as ipfile:
    iplocks = csv.DictReader(ipfile)
    for row in iplocks:
      if row['ipaddr'] == ipaddr and row['email'] == email:
        foundGuid = row['guid']
        break
  if foundGuid != "":
    with open(allGuidsCSV, encoding='utf-8') as allfile:
      allf = csv.DictReader(allfile)
      for allrow in allf:
        if allrow['guid'] == foundGuid:
          appID = allrow['appid']
          if 'sandboxzone' in allrow:
            sandboxZone = allrow['sandboxzone']
          break
  if foundGuid != "":
    redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s&sandboxzone=%s" % (myurl,profile,foundGuid,labCode,appID,sandboxZone)
    printheader(True, redirectURL, "0", operation)
    exit()
  assignedGuid = False
  #sleep(randint(1,5))
  allGuids = {}
  with open(allGuidsCSV, encoding='utf-8') as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      allGuids[allrow['guid']] = True
  ipfile = open(assignedCSV, encoding='utf-8')
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
    ipfile = open(assignedCSV, 'a', encoding='utf-8')
    ipfile.write(foundGuid + "," + ipaddr + "," + email + "\n")
    assignedGuid = True
    with open(allGuidsCSV, encoding='utf-8') as allfile:
      allf = csv.DictReader(allfile)
      for allrow in allf:
        if allrow['guid'] == foundGuid:
          appID = allrow['appid']
          if 'sandboxzone' in allrow:
            sandboxZone = allrow['sandboxzone']
          break
  fcntl.flock(ipfile, fcntl.LOCK_UN)
  if not assignedGuid:
    msg=urllib.parse.quote("Sorry, there are no available GUIDs for lab <b>{0}</b>, please double check that you selected the correct lab code or contact a lab assistant.".format(labCode))
    redirectURL="%s?profile=%s&msg=%s" % (myurl,profile,msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  else:
    redirectURL="%s?profile=%s&operation=setguid&guid=%s&labcode=%s&appid=%s&sandboxzone=%s" % (myurl,profile,foundGuid,labCode,appID,sandboxZone)
    printheader(True, redirectURL, "0")
    exit()
elif operation == "setguid":
  if 'labcode' not in form:
    printheader()
    print("ERROR, no labcode provided.")
    printback()
    printfooter()
    exit ()
  labCode = form.getvalue('labcode')
  if 'guid' not in form:
    printheader()
    print("ERROR, no guid provided.")
    printback()
    printfooter()
    exit ()
  foundGuid = form.getvalue('guid')
  #if 'appid' not in form:
  #  printheader()
  #  print("ERROR, no appid provided.")
  #  printback()
  #  printfooter()
  #  exit ()
  if 'appid' in form:
    appID = form.getvalue('appid')
  else:
    appID = ""
  if 'sandboxzone' in form:
    sandboxZone = form.getvalue('sandboxzone')
  else:
    sandboxZone = ""
  redirectURL="%s?profile=%s&operation=showguid&guid=%s&labcode=%s&appid=%s&sandboxzone=%s" % (myurl,profile,foundGuid,labCode,appID,sandboxZone)
  printheader(True, redirectURL, "0", operation, foundGuid, labCode, appID, sandboxZone)
  exit()
elif operation == "showguid":
  if 'labcode' not in form:
    printheader()
    print("Unexpected ERROR: no labcode forwarded. Please contact lab assistant.")
    printback()
    printfooter()
    exit()
  printheader(False, "", "", operation)
  guid = form.getvalue('guid')
  labCode = form.getvalue('labcode')
  if 'sandboxzone' in form:
    sandboxZone = form.getvalue('sandboxzone')
  else:
    sandboxZone = ""
  bastion = ""
  docURL = ""
  description = ""
  urls = ""
  labUser = ""
  labSSHkey = ""
  found = False
  guidType = "GUID"
  sharedGUID = ""
  shared = False
  environment = ""
  with open(labConfigCSV, encoding='utf-8') as csvFile:
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
        environment = row['environment']
        if 'shared' in row and row['shared'] != "None" and row['shared'] != "":
          guidType = "number"
          shared = True
          if 'appid' in form:
            sharedGUID = form.getvalue('appid')
        break
  if not found:
    print("Unexpected ERROR: This lab no longer exists. Please contact lab assistant.<br>")
    print("Only if <b>directed by lab assistant</b> click this button: <button onclick='rusure()'>RESET STATION</button>")
    printback()
    printfooter()
    exit()
  if 'guid' not in form:
    print(("Unexpected ERROR: no %s found. Please contact lab assistant." % guidType))
    printback()
    printfooter()
    exit()
  print("<center><table border=0>")
  print("<tr><td>")
  print(("<center><h2>Welcome to: %s</h2><table border=0>" % description))
  print(("<tr><td align=right>Your assigned lab %s is</td><td align=center><table border=1><tr><td><font size='5'><pre><b>%s</b></pre></font></td></tr></table></td></tr>" % (guidType,guid)))
  if shared and sharedGUID != "":
    print(("<tr><td align=right>Your shared lab GUID is</td><td align=center><table border=1><tr><td><font size='5'><pre><b>%s</b></pre></font></td></tr></table></td></tr>" % (sharedGUID)))
  print("</table></center>" )
  print("Let's get started! Please read these instructions carefully before starting to have the best lab experience:")
  print(("<ul><li>Save the above <b>%s</b> as you will need it to access your lab's systems from your workstation.</li>" % guidType))
  print("<li>Consult the lab instructions <i>before</i> attempting to connect to the lab environment.</li>")
  if docURL != "" and docURL != "None":
    if shared and sharedGUID != "":
      docURL = docURL.replace('REPL', sharedGUID)
      docURL = docURL.replace('X', guid)
    else:
      docURL = docURL.replace('REPL', guid)
    print(("<li>Open the lab instructions by clicking <a href='%s' target='_blank'>here</a></li>" % docURL))
  if labSSHkey != "" and labSSHkey != "None":
    print(("<li>You can download the lab SSH key from <a href='%s'>here</a>.</li>" % labSSHkey))
    print("<li>Save this key (example filename: keyfile.pem) then run <pre>chmod 0600 keyfile.pem</pre></li>")
  if bastion != "" and bastion != "None":
    if shared and sharedGUID != "":
      bastion = bastion.replace('REPL', sharedGUID)
      bastion = bastion.replace('X', guid)
    else:
      bastion = bastion.replace('REPL', guid)
    if sandboxZone != "":
      bastion = bastion.replace('DOMAIN', sandboxZone)
    if labUser != "" and labUser != "None":
      print(("<li>You will need to use the user name <b>%s</b> to log into your lab environment.</li>" % labUser))
      lu = "%s@" % labUser
    else:
      lu = ""
    if labSSHkey != "" and labSSHkey != "None":
      lk = "-i /path/to/keyfile.pem "
    else:
      lk = ""
    print(("<li>When prompted to do so by the lab instructions, you can SSH to your bastion host by opening a terminal and issuing the following command:<br><pre>$ ssh %s%s%s</pre></li>" % (lk, lu, bastion)))
    print("<li>Unless otherwise stated in the lab instructions, the password is: <pre><b>r3dh4t1!</b></pre></li>")
  else:
    #if urls != "None":
    #  print ("<li>For example, if the lab requires you to access a URL it would be like this<br><pre>https://host-{0}.rhpds.opentlc.com</pre></li>".format(guid))
    if bastion != "" and bastion != "None":
      print(("<li>If lab requires the use of the SSH command it would look like this:<br><pre>ssh host-{0}.rhpds.opentlc.com</pre></li>".format(guid)))
    #print("<li><b>Note:</b>These are <b>just examples</b>, please consult the lab instructions for actual host names and URLs.</li>")
  if urls != "" and urls != "None":
    print("<li>The following URLs will be used in your lab environment. Please only access these links when the lab instructions specify to do so:<ul>")
    for u in urls.split(";"):
      if sandboxZone != "":
        u = u.replace('DOMAIN', sandboxZone)
      if shared and sharedGUID != "":
        u = u.replace('REPL', sharedGUID)
      else:
        u = u.replace('REPL', guid)
      if u.startswith("*"):
        print(("<li>Wildcard DNS entry: <b>{0}</b></li>".format(u)))
      elif u.startswith("http"):
        print(("<li><a href='{0}' target='_blank'>{0}</a></li>".format(u)))
      elif ':' in u:
        t, u2 = u.split(':', 1)
        print("<li><b>%s:</b>&nbsp;<a href='%s' target='_blank'>%s</a></li>" % (t, u2, u2))
      else:
        print("<li><a href='http://%s' target='_blank'>http://%s</a></li>" % (u, u))
    print("<li>Note: The lab instructions may specify other host names and/or URLs.</li>")
    print("</ul>")
  if bastion == "None" and urls == "None":
    print("<li>Please consult the lab instructions for any host names and/or URLs that you may need to connect to.</li>")
  if 'appid' in form and guidType != "number":
    appid = form.getvalue('appid')
    #print("<li>You can access your detailed lab environment information at <a href='https://www.opentlc.com/summit-status/status.php?appid=%s&guid=%s' target='_blank'>here</a></li>" % (appid,guid))
    consoleURL="https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid,appid)
    print(("<li>If <b>required</b> by the lab instructions, you can reach your environment's power control and consoles by clicking: <a href='%s' target='_blank'>here</a></li>" % consoleURL))
  print("</ul></td></tr></table>")
  if environment == "spp" and profile == "generic_sko":
    print("<table border=0><tr><td align=right><font size=3>OpenShift administrator user:&nbsp;</font></td><td><font size=3><pre>admin</pre></font></td></tr>")
    print("<tr><td align=right><font size=3>OpenShift administrator password:&nbsp;</font></td><td><font size=3><pre>r3dh4t1!</pre></font></td></tr></table>")
  print("<p>When you are <b>completely finished</b> with this lab please click the <b>RESET STATION</b> button below.</p>")
  print("<button onclick='rusure()'>RESET STATION</button>")
  print("</center>")
  printfooter(operation)
else:
  printheader()
  print("Unexpected ERROR: invalid operation. Please contact lab assistant.")
  printfooter()
