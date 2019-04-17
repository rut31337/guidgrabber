#!/usr/bin/python3

import csv
import cgi
import urllib.parse
import os
import subprocess
import sys
import configparser, os
import re
import datetime
import requests
from requests.auth import HTTPBasicAuth
import shutil
from shutil import copyfile

def gettok(cfurl, cfuser, cfpass):
  response = requests.get(cfurl + "/api/auth", auth=HTTPBasicAuth(cfuser, cfpass))
  data = response.json()
  return data['auth_token']

def apicall(token, url, op, group ):
  head = {'Content-Type': 'application/json', 'X-Auth-Token': token, 'accept': 'application/json;version=2', 'X-MIQ-Group': group}
  if op == "get":
    response = requests.get(url, headers=head)
  obj = response.json()
  return obj

def manageApp(client, op, app, runTime=0):
  status = application_state(app)
  if op == "start":
    ate = 3600*runTime
    exp = {'expirationFromNowSeconds': ate}
    if status == 'STARTED' or 'STARTING' in status:
      print ("App %s is in state %s, extending runtime by %s hours.<br>" % (str(app['id']), status, str(runTime)) )
      client.set_application_expiration(app['id'], exp)
    elif 'STOPPED' in status:
      if runTime != 0:
        client.set_application_expiration(app['id'], exp)
      print ("Starting appID %s with runtime of %s hours.<br>" % (str(app['id']), str(runTime)) )
      client.start_application(app['id'])
    elif 'STOPPING' in status:
      print ("No action possible, appID %s, is in state %s.<br>" % (str(app['id']), status) )
      return True
    else:
      print ("Warning: appID %s is in an unhandled state of %s.<br>" % (str(app['id']), status) )
  elif op == "stop":
    if 'STARTED' in status:
      print ("Stopping appID %s.<br>" % (str(app['id'])) )
      client.stop_application(app['id'])
    elif 'STOPPED' in status:
      print ("appID %s is already stopped.<br>" % (str(app['id'])) )
    elif 'STARTING' in status or 'STOPPING' in status:
      print ("No action for appID %s, it is in transient state %s.<br>" % (str(app['id']), status) )
      return True
    else:
      print ("Warning: appID %s is in an unhandled state of %s.<br>" % (str(app['id']), status) )

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
    prerror("ERROR: Command failed with return code (%s)<br>OUT(%s)" % (exitCode, output))

def prerror(msg):
  print ("<center>%s<br></center>" % msg )

def printback():
  print ('<button class="w3-btn w3-white w3-border w3-padding-small" onclick="goBack()"><&nbsp;Back</button>' )

def printback2():
  impb = ""
  if impersonate:
    impb = "?impersonate=" + profile
  print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s%s'\" type=button><&nbsp;Back</button>" % (myurl, impb) )

def printback3(labCode):
  print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s%s'\" type=button><&nbsp;Back</button>" % (myurl, labCode, imp) )

def callredirect(redirectURL, waittime=0):
  print ('<head>' )
  print ('<meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL) )
  print ('</head><html><body></body></html>' )

def includehtml(fname):
  with open(fname, 'r', encoding='utf-8') as fin:
    print (fin.read())

def printheader(redirect=False, redirectURL="", waittime="0", operation="none"):
  print ("Content-type:text/html\r\n\r\n" )
  if redirect and redirectURL != "":
    callredirect(redirectURL, waittime)
    exit()
  print ('<html><head>' )
  includehtml('head-manager.inc')
  print ('</head>' )
  if "summit" in profile or profile == "generic_tester":
    includehtml('topbar-summit.inc')
  elif profile == "generic_sko":
    includehtml('topbar-sko.inc')
  else:
    includehtml('topbar-old.inc')
  includehtml('textarea-manager.inc')
  if impersonate:
    print ("<center>>>>><font color=red>Impersonating user %s</font><<<<</center>" % profile)

def printfooter(operation="none"):
  if operation is not "mainmenu":
    imph = ""
    if impersonate:
      imph = "?impersonate=" + profile
    print ('<center><button class="w3-btn w3-white w3-border w3-padding-small" onclick="window.location.href=\''+ myurl + imph + '\'">Home</button></center>' )
  if "summit" in profile or profile == "generic_tester":
    includehtml('footer-manager-summit.inc')
  else:
    includehtml('footer-manager-old.inc')
  print ('</body>' )
  print ('</html>' )
  exit()

def printform(operation="", labcode="", labname="", labkey="", bastion="", docurl="", laburls="", catname="", catitem="", labuser="", labsshkey="", environment="", blueprint="", shared="", infraWorkload="", region="", city="", salesforce="", surveyLink="", envsize="", studentWorkload="", bareMetal="", serviceType=""):
  config = configparser.ConfigParser()
  config.read(cfgfile)
  cfuser = config.get('cloudforms-credentials', 'user')
  cfpass = config.get('cloudforms-credentials', 'password')
  catalogs = {}
  if spp:
    cfurl = "https://spp.opentlc.com"
    cfgroup = "rhpds-access-spp"
  else:
    cfurl = config.get('cloudforms-credentials', 'url')
    cfgroup = config.get('cloudforms-credentials', 'group')
  token = gettok(cfurl, cfuser, cfpass)
  url = cfurl + "/api/service_catalogs?expand=resources&attributes=name"
  serviceCatalogsAll = apicall(token, url, "get", cfgroup)
  for sc in serviceCatalogsAll.get('resources'):
    catalogs[sc['id']] = sc['name']
  url = cfurl + "/api/service_templates?attributes=name,service_template_catalog_id&expand=resources"
  serviceTemplatesAll = apicall(token, url, "get", cfgroup)
  catalogItems = {}
  for st in serviceTemplatesAll.get('resources'):
    stName = st['name']
    catID = st['service_template_catalog_id']
    catalogItems[stName] = catID
  for catID in catalogs.copy():
    catEmpty = True
    for stName, stCatID in catalogItems.items():
      if stCatID == catID:
        catEmpty = False
    if catEmpty:
      catalogs.pop(catID)
  print ("<script>")
  print (" var catalogItems = {")
  for catID, catName in sorted(catalogs.items(), key=lambda x: x[1], reverse=False):
    print ("'%s': [" % catName)
    for stName, stCatID in sorted(catalogItems.items()):
      if stCatID == catID:
        print ("'%s'," % stName )
    print ( "]," )
  print ("}")
  print ("</script>")
  print ("""
  <script>
    function createOption(ddl, text, value, selected) {
        var opt = document.createElement('option');
        opt.value = value;
        opt.text = text;
        if (selected) {
          opt.selected = true;
        }
        ddl.options.add(opt);
    }
    function createOptions(optionsArray, ddl, selectedItem) {
        for (i = 0; i < optionsArray.length; i++) {
            if ( optionsArray[i] === "selectedItem" ) {
            createOption(ddl, optionsArray[i], optionsArray[i], true);
            } else {
            createOption(ddl, optionsArray[i], optionsArray[i], false);
            }
        }
    }
    function setItems(ddl1, ddl2, selectedItem) {
        ddl2.options.length = 0;
        var ddl2keys = catalogItems[ddl1.value];
        createOptions(ddl2keys, ddl2, selectedItem)
    }
</script>


""")
  print ("""
<style>
tbody.tbg {
  border: 2px solid black;
}
tr.brd{
  border-left: 2px solid black;
  border-right: 2px solid black;
}
</style>
""")
  print ('<form id="myform" method="post" action="%s?operation=%s%s">' % (myurl, operation, imp) )
  print ("<center><table width=60% border=0>")
  if operation == 'create_lab':
    print ('<tr><td colspan=2 align=center><p style="color: black; font-size: 0.6em;">There are no labs set up for your user <b>' + profile + '</b> please fill out this form to create one:</p></td></tr>' )
  if operation == 'update_lab':
    print ("<tbody class=tbg><tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Code*:</b></td><td style='font-size: 0.6em;'><input type='hidden' name='labcode' size='20' value='%s'>%s</td></tr>" % (labcode, labcode) )
  else:
    print ("<tbody class=tbg><tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Code (Alphanumeric Only)*:</b></td><td><input type='text' name='labcode' size='20'></td></tr>" )
  if spp:
    print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Name*:</b></td><td style='font-size: 0.6em;'><input type='hidden' name='labname' size='80' value='%s'>%s</td></tr>" % (labname, labname) )
  else:
    print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Name*:</b></td><td><input type='text' name='labname' size='80' value='%s'></td></tr>" %  labname )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Key*:</b></td><td><input type='text' name='labkey' size='20' value='%s'></td></tr></tbody>" % labkey )

  if spp:
    region = "na"
  print ("<tbody class=tbg><tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Region*:</b></td><td><select name='region'>")
  na = ""
  apac = ""
  emea = ""
  if region == "na":
    na = "selected"
  elif region == "apac":
    apac = "selected"
  elif region == "emea":
    emea = "selected"
  print ("<option value='na' %s>NA</option>" % na )
  print ("<option value='emea' %s>EMEA</option>" % emea)
  print ("<option value='apac' %s>APAC</option>" % apac)
  print ("</select></td></tr>")
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Environment*:</b></td><td style='font-size: 0.6em;'>" )
  if spp:
    print ("<input type='radio' name='environment' value='spp' checked >SPP" )
  else:
    print ("<input type='radio' name='environment' value='rhpds' checked >RHPDS" )
  print ("</td></tr>" )
  print ("</tbody>")

  print ("<tbody class=tbg><tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Catalog Name*:</b></td><td><select id='catname' onchange=\"setItems(this, document.getElementById('catitems'), '%s')\" name='catname'>" % catitem)
  for catid,cat in catalogs.items():
    if catname == cat:
      selected = " selected"
    else:
      selected = ""
    print ("<option value='%s' %s>%s</option>" % (cat, selected, cat) )
  print ("</select></td></tr>")
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Catalog Item*:</b></td><td><select id='catitems' name='catitem'></select></td></tr></tbody>")
  print ("<tbody class=tbg><tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Service Type*:</b></td><td align=left style='width:40%%; font-size: 0.6em;'>")
  ravc = ""
  agdc = ""
  agsc = ""
  if serviceType == 'agnosticd':
    agdc = "checked='checked'"
  elif serviceType == 'agnosticd-shared':
    agsc = "checked='checked'"
  else:
    ravc = "checked='checked'"
  print ("""
<input type="radio" name="servicetype" %s value="ravello" onclick="showRavello()"/>&nbsp;Ravello&nbsp;|&nbsp;
<input type="radio" name="servicetype" %s value="agnosticd" onclick="showAgnosticD()"/>&nbsp;AgnosticD Dedicated&nbsp;|&nbsp;
<input type="radio" name="servicetype" %s value="agnosticd-shared" onclick="showAgnosticDshared()"/>AgnosticD Shared
</td></tr></tbody>
""" % (ravc,agdc,agsc))
  print ("<tbody id='ravello' style='display:none;'><tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Blueprint*:</b></td><td><input type='text' name='blueprint' size='80' value='%s'></td></tr>" %  blueprint )
  bmt = ""
  bmf = ""
  if bareMetal == "t":
    bmt = "checked='checked'"
  else:
    bmf = "checked='checked'"
  print ("<tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Bare Metal (Nested Virt)*:</b></td><td align=left style='width:40%%; font-size: 0.6em;'>")
  #print ("<td><input type='text' name='baremetal' size='80' value='%s'></td></tr></tbody>" %  bareMetal )
  print ("""
<input type="radio" name="baremetal" %s value="t"/>&nbsp;True&nbsp;|&nbsp;
<input type="radio" name="baremetal" %s value="f"/>&nbsp;False
</td></tr>
""" % (bmt,bmf))

  print ("<tbody id='agnosticd' style='display:none;'><tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Infra Workload*:</b></td><td><input type='text' name='infraworkload' size='80' value='%s'></td></tr>" %  infraWorkload )
  print ("<tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Student Workload*:</b></td><td><input type='text' name='studentworkload' size='80' value='%s'></td></tr>" %  studentWorkload )
  print ("<tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Size*</b></td><td><select name='envsize'>")
  default = ""
  small = ""
  if envsize == "small":
    small = "selected"
  else:
    default = "selected"
  print ("<option value='default' %s>Default</option>" % default)
  print ("<option value='small' %s>Small</option>" % small)
  print ("</select></td></tr></tbody>")
  print ("<tbody id='agnosticd-shared' style='display:none;'>")
  print ("<tr class=brd><td align=right style='width:40%%; font-size: 0.6em;'><b>Shared User Count*:</b></td><td><input type='text' name='shared' size='80' value='%s'></td></tr></tbody>" % shared  )
  if spp:
    city = "boston"
    salesforce = "summit"
    print ("<input type='hidden' name='city' size='80' value='%s'>" % (city) )
    print ("<input type='hidden' name='salesforce' size='80' value='%s'>" % (salesforce) )
  else:
    print ("<tbody class=tbg>")
    print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Event City (lowercase/no spaces):</b></td><td><input type='text' name='city' size='80' value='%s'></td></tr>" % city )
    print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Salesforce Opportunity ID (If you have one):</b></td><td><input type='text' name='salesforce' size='80' value='%s'></td></tr>" % salesforce )
    print ("</tbody>")

  print ("<tbody class=tbg>")
  print ("<tr><td align=center style='font-size: 0.6em;' colspan=2><b>NOTE:</b> For all fields specifying FQDN or URL you can use the string <b>REPL</b> which will be replaced by GUID (ex. bastion-REPL.rhpds.opentlc.com)</td></tr>" )
  print ("<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about SSH in your GUID page</td></tr>" )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Bastion FQDN:</b></td><td><input type='text' name='bastion' size='40' value='%s'></td></tr>" % bastion )
  print ("<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about SSH keys.</td></tr>" )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab SSH Key URL:</b></td><td><input type='text' name='labsshkey' size='80' value='%s'></td></tr>" % labsshkey )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab User Login:</b></td><td><input type='text' name='labuser' size='80' value='%s'></td></tr>" % labuser )
  print ("</tbody>")
  print ("<tbody class=tbg>")
  print ("<tr><td colspan=2 align=center style='font-size: 0.6em;'>Enter <b>None</b> below if you don't want to print anything about URLs in your GUID page</td></tr>" )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Semicolon Delimited List of Lab URLs (ex. https://www-REPL.rhpds.opentlc.com) if http/https not provided, http assumed:</b></td><td><textarea cols='80' name='laburls'>%s</textarea></td></tr>" % laburls )
  print ("</tbody>")
  print ("<tbody class=tbg>")
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Lab Documentation URL:</b></td><td><input type='text' name='docurl' size='80' value='%s'></td></tr>" % docurl )
  print ("<tr><td align=right style='width:40%%; font-size: 0.6em;'><b>Survey Link URL:</b></td><td><input type='text' name='surveylink' size='80' value='%s'></td></tr>" % surveyLink )
  print ("</tbody><tbody>")
  print ('<tr><td colspan=2 align=center>' )
  printback2()
  print ('<input class="w3-btn w3-white w3-border w3-padding-small" type="submit" value="Next&nbsp;>"></td></tr></tbody></table>' )
  print ('</center></form>' )
  print ("<script>")
  print ("window.onload = setItems(document.getElementById('catname'), document.getElementById('catitems'), '%s');" % catitem)
  print ("</script>")
  if catname != "":
    print ("<script>")
    print ("window.onload = createOption(document.getElementById('catitems'), '%s', '%s', true);" % (catitem, catitem))
    print ("</script>")
  if serviceType == "agnosticd":
    print ("<script>document.getElementById('agnosticd').style.display='table-row-group';</script>")
  elif serviceType == "agnosticd-shared":
    print ("<script>document.getElementById('agnosticd').style.display='table-row-group';</script>")
    print ("<script>document.getElementById('agnosticd-shared').style.display='table-row-group';</script>")
  else:
    print ("<script>document.getElementById('ravello').style.display='table-row-group';</script>")
  print ("""
<script>
function showRavello(){
  document.getElementById('ravello').style.display ='table-row-group';
  document.getElementById('agnosticd').style.display = 'none';
  document.getElementById('agnosticd-shared').style.display = 'none';
}
function showAgnosticD(){
  document.getElementById('ravello').style.display ='none';
  document.getElementById('agnosticd').style.display = 'table-row-group';
  document.getElementById('agnosticd-shared').style.display = 'none';
}
function showAgnosticDshared(){
  document.getElementById('ravello').style.display ='none';
  document.getElementById('agnosticd').style.display = 'table-row-group';
  document.getElementById('agnosticd-shared').style.display = 'table-row-group';
}
</script>
""")
if not os.environ.get('REMOTE_USER'): 
  printheader()
  prerror("ERROR: No profile specified.")
  printfooter()
  exit()
else:
  profile = os.environ.get('REMOTE_USER')
if profile == "generic_tester" or profile == "generic_sko" or profile == "generic_summit":
  spp = True
  myurl = "/gg/manager-spp.cgi"
else:
  spp = False
  myurl = "/gg/manager.cgi"

ggurl = "https://www.opentlc.com/gg/gg.cgi"
ggroot = "/var/www/guidgrabber"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/bin/"
cfgfile = ggetc + "gg.cfg"

admin = False
c = configparser.ConfigParser()
c.read(cfgfile)
admins = c.get('manager-admins', 'users').split(',')
if profile in admins:
  admin = True

form = cgi.FieldStorage()

imp = ""
impersonate = False
if admin:
  if 'impersonate' in form:
    impersonate = True
    profile = form.getvalue('impersonate')
    imp = "&impersonate=" + profile 

profileDir = ggetc + "/" + profile
if not os.path.isdir(profileDir):
  os.mkdir(profileDir)
labConfigCSV = profileDir + "/labconfig.csv"
labCSVheader = "code,description,activationkey,bastion,docurl,urls,catname,catitem,labuser,labsshkey,environment,blueprint,shared,infraworkload,region,city,salesforce,surveylink,envsize,studentworkload,baremetal,servicetype\n"

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
  print ("<center><table border=0><tr valign=top><td><table border=0>" )
  if 'msg' in form:
    print ('<tr><td><p style="color: black; font-size: .7em;">' + form.getvalue('msg') + "</p></td></tr>" )
  print ("<tr><td style='font-size: .7em;' colspan=2>Choose an operation <b>%s</b>:</td></tr>" % profile )
  if not spp:
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=create_new_lab_form%s>Add A New Lab Configuration</a></td></tr>" % (myurl, imp) )
  found = False
  with open(labConfigCSV, encoding='utf-8') as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      else:
        found = True
        break
  if os.path.exists(labConfigCSV) and found:
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=edit_lab%s>View/Edit Lab Configuration</a></td></tr>" % (myurl, imp) )
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=deploy_lab%s>Deploy Lab Instances</a></td></tr>" % (myurl, imp) )
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=update_guids%s>Update Available Lab GUIDs</a></td></tr>" % (myurl, imp) )
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=choose_lab%s>Manage Lab</a></td></tr>" % (myurl, imp) )
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=delete_instance%s>Delete Lab Instances</a></td></tr>" % (myurl, imp) )
    if not spp:
      print ("<tr><td style='font-size: .7em;'><a href=%s?operation=delete_lab%s>Delete Lab Configuration</a></td></tr>" % (myurl, imp) )
  print ('</table></td>')
  if admin:
    print ("<td><table border=0><tr><td style='font-size: .7em;'>Admin Functions:</td></tr>")
    print ("<tr><td style='font-size: .7em;'><a href=%s?operation=impersonate>Impersonate User</a></td></tr>" % myurl )
    if impersonate:
      print ("<tr><td style='font-size: .7em;'><a href=%s>Un-Impersonate User</a></td></tr>" % myurl )
    print ("</table></td>")
  print ('</tr></table>')
  if os.path.exists(labConfigCSV) and found:
    print ("<p style='font-size: 0.8em;'>Share this link with your attendees:<br><b>%s?profile=%s</b><br>TIP: Use bit.ly or similar tool to shorten link.</p>" % (ggurl, profile) )
  print ('</center>')
  printfooter("mainmenu")
  exit()
elif operation == "create_new_lab_form":
  printheader()
  printform('create_new_lab')
  printfooter()
  exit()
elif operation == "choose_lab" or operation == "edit_lab" or operation == "delete_lab" or operation == "update_guids" or operation == "deploy_lab" or operation == "delete_instance":
  printheader()
  print ("<center><table border=0>" )
  if 'msg' in form:
    print ('<tr><td><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr>" )
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
  print ('<form method="post" action="%s?operation=%s%s">' % (myurl, op2, imp) )
  print ('<tr><td colspan=2 align=center><p style="color: black; font-size: .8em;">Please choose the lab you wish to %s:</p></td></tr>' % op )
  print ("<tr><td colspan=2 align=center style='font-size: .6em;'><select name='labcode'>" )
  with open(labConfigCSV, encoding='utf-8') as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      print('<option value="{0}">{0} - {1}</option>'.format(row['code'],row['description']))
  print ("</select></td></tr>" )
  if operation == 'update_guids':
    print ("<tr><td align=center style='font-size: 0.6em;'><b>Delete Assigned GUIDs:&nbsp;</b><input type='checkbox' name='delete_assigned'></td></tr>" )
  if operation == 'deploy_lab':
    print ("<tr><td align=right style='font-size: 0.6em;'><b>Number of instances to deploy:&nbsp;</b></td>")
    print ("<td><input type='text' name='num_instances' size='2'></td></tr>" )
    if spp:
      config = configparser.ConfigParser()
      config.read(cfgfile)
      sppPass = config.get('spp', 'password')
      print ("<tr><td align=right style='font-size: 0.6em;'><td><input type='hidden' name='cfpass' value='%s'></td></tr>" % (sppPass))
    else:
      print ("<tr><td align=right style='font-size: 0.6em;'><b>Password for user %s:</b></td><td><input type='password' name='cfpass' size='8'></td></tr>" % (profile) )
  print ('<tr><td colspan=2 align=center>' )
  printback2()
  print ('<input class="w3-btn w3-white w3-border w3-padding-small" type="submit" value="Next&nbsp;>"></td></tr>' )
  print ('</form></table></center>' )
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
    with open(labConfigCSV, "w", encoding='utf-8') as conffile:
      conffile.write(labCSVheader)
  else:
    with open(labConfigCSV, encoding='utf-8') as conffile:
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
  infraWorkload = form.getvalue('infraworkload')
  studentWorkload = form.getvalue('studentworkload')
  envsize = form.getvalue('envsize')
  region = form.getvalue('region')
  if 'city' in form:
    city = form.getvalue('city')
    city = city.replace(" ", "")
    city = city.lower()
  else:
    city = ""
  salesforce = form.getvalue('salesforce')
  surveyLink = form.getvalue('surveylink')
  bareMetal = form.getvalue('baremetal')
  serviceType = form.getvalue('servicetype')
  ln = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (labCode, labName, labKey, bastion, docURL, labURLs, catName, catItem, labUser, labSSHkey, environment, blueprint, shared, infraWorkload, region, city, salesforce, surveyLink, envsize, studentWorkload, bareMetal, serviceType)
  with open(labConfigCSV, "a", encoding='utf-8') as conffile:
    conffile.write(ln)
  ms="Lab <b>%s - %s</b> Has Been Created<ul style='color: black; font-size: .7em;'><li>Please copy this link: <b>%s?profile=%s</b></li><li>You should create a short URL for this link and provide it to your users.</li><li>Next step is to use <b>Deploy Lab Instances</b> below.</li></ul>" % (labCode, labName, ggurl, profile)
  msg=urllib.parse.quote(ms)
  redirectURL="%s?msg=%s%s" % (myurl, msg, imp)
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
  with open(labConfigCSV, encoding='utf-8') as csvFile:
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
  redirectURL = "%s?operation=%s&labcode=%s%s" % (myurl, op, labCode, imp)
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
  with open(labConfigCSV, encoding='utf-8') as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'] == labCode:
        if 'shared' not in row:
          row['shared'] = ""
        printheader()
        if 'blueprint' not in row:
          blueprint = ""
        else:
          blueprint = row['blueprint']
        if 'shared' not in row:
          shared = ""
        else:
          shared = row['shared']
        if 'infraworkload' not in row:
          infraWorkload = ""
        else:
          infraWorkload = row['infraworkload']
        if 'studentworkload' not in row:
          studentWorkload = ""
        else:
          studentWorkload = row['studentworkload']
        if 'envsize' not in row:
          envsize = ""
        else:
          envsize = row['envsize']
        if 'region' not in row:
          region = ""
        else:
          region = row['region']
        if 'city' not in row:
          city = "unknown"
        else:
          city = row['city']
        if 'salesforce' not in row:
          salesforce = "unknown"
        else:
          salesforce = row['salesforce']
        if 'surveylink' not in row:
          surveyLink = ""
        else:
          surveyLink = row['surveylink']
        if 'baremetal' not in row:
          bareMetal = ""
        else:
          bareMetal = row['baremetal']
        if 'servicetype' not in row:
          serviceType = ""
        else:
          serviceType = row['servicetype']
        printform('update_lab', row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], blueprint, shared, infraWorkload, region, city, salesforce, surveyLink, envsize, studentWorkload, bareMetal, serviceType)
        printfooter()
        exit()
  printheader()
  prerror("ERROR: Labcode %s not found.<br><center>" % (labCode))
  printfooter()
  exit()
elif operation == "power_on" or operation == "power_off":
  printheader()
  if 'labcode' not in form:
    print ("ERROR, no labcode provided." )
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
  config = configparser.ConfigParser()
  config.read(cfgfile)
  ravUser = config.get('ravello-credentials', 'user')
  ravPw = config.get('ravello-credentials', 'password')
  ravDom = config.get('ravello-credentials', 'domain')
  from ravello_sdk import *
  client = RavelloClient()
  try:
    client.login(ravUser, ravPw, ravDom)
  except:
    prerror('Error: Unable to connect to Ravello or invalid user credentials')
  with open(allGuidsCSV, encoding='utf-8') as allfile:
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
elif operation == "view_lab" or operation == "del_lab" or operation == "update_lab" or operation == "release_all_guids":
  if 'labcode' not in form:
    printheader()
    prerror("ERROR: No labcode provided.")
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  allGuidsCSV = profileDir + "/availableguids-" + labCode + ".csv"
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  if operation == "release_all_guids":
    if os.path.exists(assignedCSV):
      os.remove(assignedCSV)
    redirectURL = "%s?operation=view_lab&labcode=%s%s" % (myurl, labCode, imp)
    printheader(True, redirectURL, "1")
    printfooter()
    exit()
  if operation == "del_lab" or operation == "update_lab":
    oldConfFile = open(labConfigCSV, encoding='utf-8')
    old = oldConfFile.readlines()
    oldConfFile.close()
    newLabConfigCSV = labConfigCSV + ".tmp"
    with open(newLabConfigCSV, "w", encoding='utf-8') as newConfFile:
      newConfFile.write(labCSVheader)
    newConfFile.close()
    newConfFile = open(newLabConfigCSV,"a", encoding='utf-8')
    labcodes = csv.DictReader(old)
    if operation == "del_lab":
      for row in labcodes:
        if row['code'] != labCode:
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], row['blueprint'], row['shared'], row['infraworkload'], row['region'], row['city'], row['salesforce'], row['surveylink'], row['envsize'], row['studentworkload'], row['baremetal'], row['servicetype'])
          newConfFile.write(out)
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
          infraWorkload = form.getvalue('infraworkload')
          studentWorkload = form.getvalue('studentworkload')
          envsize = form.getvalue('envsize')
          region = form.getvalue('region')
          city = form.getvalue('city')
          city = city.replace(" ", "")
          city = city.lower()
          salesforce = form.getvalue('salesforce')
          surveyLink = form.getvalue('surveylink')
          bareMetal = form.getvalue('baremetal')
          serviceType = form.getvalue('servicetype')
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (labCode, labName, labKey, bastion, docURL, labURLs, catName, catItem, labUser, labSSHkey, environment, blueprint, shared, infraWorkload, region, city, salesforce, surveyLink, envsize, studentWorkload, bareMetal, serviceType)
        else:
          out = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['docurl'], row['urls'], row['catname'], row['catitem'], row['labuser'], row['labsshkey'], row['environment'], row['blueprint'], row['shared'], row['infraworkload'], row['region'], row['city'], row['salesforce'], row['surveylink'], row['envsize'], row['studentworkload'], row['baremetal'], row['servicetype'])
        newConfFile.write(out)
    newConfFile.close()
    for x in reversed(range(1, 5)):
      lcb = labConfigCSV + "." + str(x)
      if os.path.exists(lcb):
        y = x + 1
        lcbn = labConfigCSV + "." + str(y)
        shutil.move(lcb, lcbn)
    labConfigCSVbak = labConfigCSV + ".1"
    copyfile(labConfigCSV, labConfigCSVbak)
    shutil.move(newLabConfigCSV, labConfigCSV)
    redirectURL = "%s?operation=none%s" % (myurl, imp)
    printheader(True, redirectURL, "0")
    printfooter()
    exit()
  asg = 0
  tot = 0
  rowc = 0
  maxrow = 10
  if not os.path.exists(allGuidsCSV):
    msg=urllib.parse.quote("ERROR: No guids for lab code <b>{0}</b> exist.<br><center>".format(labCode))
    redirectURL="%s?msg=%s" % (myurl, msg)
    printheader(True, redirectURL, "0", operation)
    printfooter()
    exit()
  printheader()
  print ("<center><b>Lab %s<b><table border=1 style='border-collapse: collapse;'>" % labCode )
  ravello = False
  with open(allGuidsCSV, encoding='utf-8') as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      if 'servicetype' in allrow and allrow['servicetype'] == 'ravello':
        ravello = True
  if ravello:
    config = configparser.ConfigParser()
    config.read(cfgfile)
    ravUser = config.get('ravello-credentials', 'user')
    ravPw = config.get('ravello-credentials', 'password')
    ravDom = config.get('ravello-credentials', 'domain')
    from ravello_sdk import *
    client = RavelloClient()
    try:
      client.login(ravUser, ravPw, ravDom)
    except:
      prerror('Error: Unable to connect to Ravello or invalid user credentials')
  with open(allGuidsCSV, encoding='utf-8') as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      status = ""
      runTime = ""
      tot = tot + 1
      if rowc == 0:
        print ("<tr>" )
      print ("<td>" )
      print ("<table border=0 width=100%>" )
      guid = allrow['guid']
      serviceType = ""
      if 'servicetype' in allrow:
        serviceType = allrow['servicetype']
      print ("<tr><td class=ggm><a href='%s?operation=manage_guid&guid=%s&labcode=%s%s'>%s</b></td></tr>" % (myurl, guid, labCode, imp, guid) )
      if serviceType == "ravello":
        appID = allrow['appid']
        try:
          app = client.get_application(appID)
          foundApp = True
        except:
          prerror('APP ID %s not found in cloud.' % (str(appID)))
          foundApp = False
        if foundApp and app:
          status = application_state(app)
          if app['published']:
            deployment = app['deployment']
            if deployment['totalActiveVms'] > 0:
              if not 'expirationTime' in deployment:
                runTime = "Never"
              else:
                expirationTime = datetime.datetime.utcfromtimestamp(deployment['expirationTime'] / 1e3)
                delta = expirationTime - datetime.datetime.utcnow()
                (h,m) = str(delta).split(':')[:2]
                runTime = "%s:%s" % (h, m)
          ravurl = "https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid, appID)
          print ("<tr><td align=center style='font-size: 0.6em;'><a href='%s' target='_blank'>Lab Dashboard</a></td></tr>" % ravurl )
        else:
          status = "ERROR: Non-Existant App In Ravello"
      assigned = False
      locked = False
      email = ""
      ipaddr = ""
      if os.path.exists(assignedCSV):
        with open(assignedCSV, encoding='utf-8') as ipfile:
          iplocks = csv.DictReader(ipfile)
          for row in iplocks:
            if row['guid'] == guid:
              foundGuid = row['guid']
              assigned = True
              if 'email' in row:
                email = row['email']
              if 'ipaddr' in row:
                ipaddr = row['ipaddr']
                if ipaddr == "locked":
                  locked = True
              #print ('<tr><td><a href="vnc://%s">Remote Desktop</a></td></tr>' % ipaddr )
              asg = asg + 1
              break
      if assigned and not locked:
        print ("<tr><td class=ggm-g>Assigned</td></tr>" )
      elif locked:
        print ("<tr><td class=ggm-r>Locked</td></tr>" )
      else:
        print ("<tr><td class=ggm-b>Unassigned</td></tr>" )
      if status != "":
        if status == "STARTED":
          color = "green"
        elif status == "STOPPED" or status == "ERROR: Non-Existant":
          color = "red"
        else:
          color = "gray"
        print ("<tr><td align=center style='font-size: 0.6em; color: %s;'>%s</td></tr>" % (color, status) )
      if runTime != "":
        print ("<tr><td align=center style='font-size: 0.6em;'>Time Left: %s</td></tr>" % (runTime) )
      if ipaddr != "":
        print ("<tr><td align=center style='font-size: 0.6em;'>IP Address: %s</td></tr>" % (ipaddr) )
      if email != "":
        print ("<tr><td align=center style='font-size: 0.6em;'>E-Mail: %s</td></tr>" % (email) )
      print ("</table>" )
      print ("</td>" )
      rowc = rowc + 1
      if rowc == maxrow:
        print ("</tr>" )
        rowc = 0
  print ("</table>" )
  print ("<table border=0>" )
  print ("<tr><th style='font-size: 0.6em;'>Total Labs:</th><td style='font-size: 0.6em;'>%s</td>" % tot )
  print ("<th style='font-size: 0.6em;'>Assigned Labs:</th><td style='font-size: 0.6em;'>%s</td>" % asg )
  avl = tot - asg
  print ("<th style='font-size: 0.6em;'>Available Labs:</th><td style='font-size: 0.6em;'>%s</td></tr>" % avl )
  print ("<tr><th colspan=6 style='font-size: 0.6em;'>Click a GUID to manage it.</td></tr>")
  print ("<tr><td colspan=6 align=center>" )
  if ravello:
    print ("""
<script>
function pwrOnWarn() {
    var runtime = prompt("Enter new runtime (in hours) and click OK.", "8");
    if (runtime == null || runtime == "") {
      txt = "Cancelled";
    } else {
      window.location.href = "%s?profile=%s&operation=power_on&labcode=%s&runtime=" + runtime + "%s";
    }
}
</script>
""" % (myurl, profile, labCode, imp))
    print ("""
<script>
function pwrOffWarn() {
    var txt;
    if (confirm("DANGER: Are you sure you wish to immediately power OFF all of your instances?  If you are sure click OK below otherwise, click Cancel.")) {
      window.location.href = "%s?profile=%s&operation=power_off&labcode=%s" + "%s";
    }
}
""" % (myurl, profile, labCode, imp))
    print ("""
function releaseAllWarn() {
    var txt;
    if (confirm("DANGER: This will release ALL assigned GUIDs?  It could result in users getting GUIDs that were assigned previously.  After this, you should Update Available Lab GUIDs.  If you are sure click OK below otherwise, click Cancel.")) {
      window.location.href = "%s?profile=%s&operation=release_all_guids&labcode=%s%s";
    }
}
</script>
""" % (myurl, profile, labCode, imp))
    print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick='pwrOnWarn()'>Power ON All Instances/Extend Runtime</button>" )
    print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick='pwrOffWarn()'>Power OFF All Instances</button>" )
    print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=get_guids&labcode=%s%s'\" type=button>Update Available Lab GUIDs</button>" % (myurl, labCode, imp) )
  print ("</td></tr>" )
  print ("<tr><td colspan=6 align=center>" )
  printback2()
  print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"history.go(0)\" type=button>Refresh</button></td></tr>" )
  print ("</table></center>" )
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
  assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
  catName = ""
  catItem = ""
  environment = ""
  shared = ""
  blueprint = ""
  infraWorkload = ""
  studentWorkload = ""
  envsize = ""
  region = ""
  city = "unknown"
  salesforce = "unknown"
  surveyLink = ""
  bareMetal = ""
  serviceType = ""
  with open(labConfigCSV, encoding='utf-8') as csvFile:
    labcodes = csv.DictReader(csvFile)
    for row in labcodes:
      if row['code'] == labCode:
        catName = row['catname']
        catItem = row['catitem']
        environment = row['environment']
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
        if 'shared' in row and row['shared'] is not None and row['shared'] != "None":
          shared = row['shared']
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
    assignedCSV = profileDir + "/assignedguids-" + labCode + ".csv"
    if 'delete_assigned' in form:
      deleteAssigned = form.getvalue('delete_assigned')
      if deleteAssigned == "on":
        if os.path.exists(assignedCSV):
          print ("<center>Deleting assigned users...")
          os.remove(assignedCSV)
    if os.path.exists(allGuidsCSV):
      os.remove(allGuidsCSV)
    if shared != "" and shared != "None":
      print ("<center>Searching for GUID for lab code %s" % labCode )
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
        printback()
        printfooter()
        exit()
      print ("<center>Creating %s shared users..." % shared )
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
      print ("<br><button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s%s'\" type=button>View Lab&nbsp;></button>" % (myurl, labCode, imp) )
    else:
      print ("<center>Please wait, getting GUIDs..." )
      print ("<pre>" )
      getguids = ggbin + "getguids.py"
      config = configparser.ConfigParser()
      config.read(cfgfile)
      cfuser = config.get('cloudforms-credentials', 'user')
      cfpass = config.get('cloudforms-credentials', 'password')
      #print ("DEBUG: %s --cfurl %s --cfuser %s --cfpass %s --catalog %s --item %s --out %s --ufilter %s" % (getguids, envirURL, cfuser, cfpass, catName, catItem, allGuidsCSV, profile))
      if spp:
        execute([getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allGuidsCSV, "--ufilter", profile, "--labcode", labCode])
      else:
        execute([getguids, "--cfurl", envirURL, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allGuidsCSV, "--ufilter", profile])
      print ("</pre>" )
      if not os.path.exists(allGuidsCSV):
        prerror("ERROR: Updating GUIDs failed in environment <b>%s</b>." % (environment))
      else:
        num_lines = sum(1 for line in open(allGuidsCSV)) - 1
        if num_lines < 1:
          print ("We were able to find the catalog and catalog item, however it appears you do not have any services completely deployed in <b>%s</b> under your account <b>%s</b>.  If the services are still deploying you may need to try again later.  Also, make sure you didn't forget to deploy lab instances." % (environment, profile) )
        else:
          print ("Success! <b>%s</b> GUIDs defined for lab <b>%s</b><br>" % (str(num_lines), labCode) )
          printback2()
          print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=view_lab&labcode=%s%s'\" type=button>View Lab&nbsp;></button>" % (myurl, labCode, imp) )
      print ("</center>" )
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
      prerror("ERROR: Number of instances must be a valid number <= 55.")
      printback()
      printfooter()
      exit()
    if int(num_instances) < 1 or int(num_instances) > 55:
      printheader()
      prerror("ERROR: Number of instances must be a positive number <= 55.")
      printback()
      printfooter()
      exit()
    printheader()
    print ("Attempting to deploy <b>%s</b> instances of <b>%s/%s</b> in environment <b>%s</b>.<br><pre>" % (num_instances, catName, catItem, environment) )
    ordersvc = ggbin + "order_svc.sh"
    settings = "check=t;expiration=7;runtime=8;labCode=%s;city=%s;salesforce=%s;notes=Deployed_With_GuidGrabber" % (labCode, city, salesforce)
    if spp:
      if serviceType == "ravello":
        settings = settings + ";autostart=t;noemail=t;pwauth=t"
        if blueprint != "":
          settings = "%s;blueprint=%s" % (settings, blueprint)
        if bareMetal != "":
          settings = "%s;bm=%s" % (settings, bareMetal)
      if serviceType == "agnosticd" or serviceType == "agnosticd-shared":
        if infraWorkload != "":
          settings = "%s;infra_workloads=%s" % (settings, infraWorkload)
        if studentWorkload != "":
          settings = "%s;student_workloads=%s" % (settings, studentWorkload)
        if envsize != "":
          settings = "%s;envsize=%s" % (settings, envsize)
        settings = settings + ";users=1"
      if serviceType == "agnosticd-shared":
        if shared != "":
          settings = "%s;users=%s" % (settings, shared)
    if region != "":
      if serviceType == "agnosticd-shared":
        settings = "%s;region=%s_shared" % (settings, region)
      else:
        settings = "%s;region=%s" % (settings, region)
    #print ( "DEBUG: %s" % (settings))
    execute([ordersvc, "-w", envirURL, "-u", profile, "-P", cfpass, "-c", catName, "-i", catItem, "-t", num_instances, "-n", "-d", settings])
    print ("</pre><center>" )
    print ("If deployment started successfully, wait at least 20 minutes from the output of this message (to complete deployment and GUID generation) then click <a href=%s?operation=update_guids%s>here</a> to update available the available GUIDs database.  Optionally you can use <b>Update Available Lab GUIDs</b> from the main menu.<br><center>" % (myurl, imp) )
    printfooter()
    exit()
  elif operation == "delete_instances":
    printheader()
    print ("Attempting to delete all deployed instances of <b>%s/%s</b> in environment <b>%s</b>.<br><pre>" % (catName, catItem, environment) )
    retiresvc = ggbin + "retire_svcs.sh"
    config = configparser.ConfigParser()
    config.read(cfgfile)
    cfuser = config.get('cloudforms-credentials', 'user')
    cfpass = config.get('cloudforms-credentials', 'password')
    if spp:
      cmd = [retiresvc, "-w", envirURL, "-u", cfuser, "-P", cfpass, "-f", profile, "-c", catName, "-i", catItem, "-l", labCode, "-n"]
    else:
      cmd = [retiresvc, "-w", envirURL, "-u", cfuser, "-P", cfpass, "-f", profile, "-c", catName, "-i", catItem, "-n"]
    # DEBUG ONLY!
    #print (cmd)
    execute(cmd)
    print ("</pre><center>Retirement Queued.<br>" )
    printback2()
    print ("<button class='w3-btn w3-white w3-border w3-padding-small' onclick=\"location.href='%s?operation=dellc&labcode=%s%s'\" type=button>Delete Lab Configuration&nbsp;></button>" % (myurl, labCode, imp) )
    print ("</center>" )
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
    with open(assignedCSV, encoding='utf-8') as ipfile:
      iplocks = csv.DictReader(ipfile)
      for row in iplocks:
        if row['guid'] == guid:
          ipaddr = row['ipaddr']
          if ipaddr == "locked":
            locked = True
          break
  printheader()
  print ("<center><table>" )
  print ("<tr><td style='font-size: .6em;' colspan=2>Choose a operation for GUID <b>%s</b>, <b>%s</b>:</td></tr>" % (guid, profile) )
  if not locked:
    print ("<tr><td style='font-size: .6em;'><a href=%s?operation=lock_guid&guid=%s&labcode=%s%s>Lock GUID Availability</a> - Remove GUID from available pool. This will release current user (if any) as well!</td></tr>" % (myurl, guid, labCode, imp) )
  print ("<tr><td style='font-size: .6em;'><a href=%s?operation=release_guid&guid=%s&labcode=%s%s>Release GUID</a> - Make GUID generally available even if already in use <font color=red>(Danger!)</font></td></tr>" % (myurl, guid, labCode, imp) )
  print ("<tr><td colspan=2 align=center>" )
  printback3(labCode)
  print ('</td></tr>' )
  print ('</table></center>' )
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
      with open(assignedCSV, "w", encoding='utf-8') as conffile:
        conffile.write(ln)
    ln = '"%s","locked"\n' % (guid)
    with open(assignedCSV, "a", encoding='utf-8') as conffile:
      conffile.write(ln)
  print ("<center>" )
  if operation == "lock_guid":
    print ("GUID <b>%s</b> Locked<br>" % guid )
  elif operation == "release_guid":
    print ("GUID <b>%s</b> Released<br>" % guid )
  print ("Remember: If a user was assigned this GUID, make sure they use the <b>Reset Station</b> button to obtain a new GUID!<br>" )
  printback3(labCode)
  print ("</center>" )
  printfooter()
  exit()
elif operation == "impersonate":
  printheader()
  print ('<form id="myform" method="post" action="%s">' % (myurl) )
  print ("<center><table>")
  print ("<tr><td align=right style='font-size: 0.6em;'><b>User To Impersonate:</b></td><td><input type='text' name='impersonate' size='20'></td></tr>" )
  print ("</table></center></form>")
else:
  printheader()
  prerror("ERROR: Invalid operation.")
  printback()
  printfooter()
  exit()
