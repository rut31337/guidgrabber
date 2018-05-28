#!/usr/bin/python

import csv
import cgi
import urllib
import os
from subprocess import call
import ConfigParser, os

def printback():
  print '<button onclick="goBack()"><&nbsp;Back</button>'

def printback2():
  print "<button onclick=\"location.href='%s'\" type=button><&nbsp;Back</button>" % myurl

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
  includehtml('footer.inc')
  print '</body>'
  print '</html>'
  exit()

def printform(operation="", labcode="", labname="", labkey="", bastion="", docurl="", laburls=""):
  print "<center><table>"
  if operation == 'create_lab':
    print '<tr><td colspan=2 align=center><p style="color: black; font-size: 0.6em;">There are no labs set up for your user <b>' + profile + '</b> please fill out this form to create one:</p></td></tr>'
  print '<tr><td><form method="post" action="%s?operation=%s">' % (myurl, operation)
  print "<table border=0>"
  if operation == 'update_lab':
    print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Code*:</b></td><td><input type='hidden' name='labcode' size='20' value='%s'>%s</td></tr>" % (labcode, labcode)
  else:
    print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Code*:</b></td><td><input type='text' name='labcode' size='20'></td></tr>"
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Name*:</b></td><td><input type='text' name='labname' size='80' value='%s'></td></tr>" %  labname
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Key*:</b></td><td><input type='text' name='labkey' size='20' value='%s'></td></tr>" % labkey
  print "<tr><td align=right style='font-size: 0.6em;'><b>Bastion FQDN:</b></td><td><input type='text' name='bastion' size='40' value='%s'></td></tr>" % bastion
  print "<tr><td align=right style='font-size: 0.6em;'><b>Lab Documentation URL:</b></td><td><input type='text' name='docurl' size='80' value='%s'></td></tr>" % docurl
  print "<tr><td align=right style='font-size: 0.6em;'><b>Semicolon Delimited List of Lab URLs (ex. https://www-REPL.rhpds.opentlc.com):</b></td><td><textarea cols='80' name='laburls'>%s</textarea></td></tr>" % laburls
  print '<tr><td align=right>'
  printback2()
  print '</td>'
  print '<td align=left><input type="submit" value="Next&nbsp;>"></td></tr></table>'
  print "</form></td></tr>"
  print '</table></center>'

if not os.environ.get('REMOTE_USER'): 
  printheader()
  print "ERROR: No profile specified."
  printfooter()
  exit()
else:
  profile = os.environ.get('REMOTE_USER')

myurl = "/gg/manager.cgi"
ggroot = "/var/www/guidgrabber"
ggetc = ggroot + "/etc/"
ggbin = ggroot + "/bin/"
cfgfile = ggetc + "/gg.cfg"

labcsv = ggetc + profile + "-labconfig.csv"

form = cgi.FieldStorage()
if 'operation' in form:
  operation = form.getvalue('operation')
else:
  operation = "none"

if operation == "none":
  if not os.path.exists(labcsv):
    printheader()
    printform('create_lab')
    printfooter()
    exit()
  printheader()
  print "<center><table>"
  if 'msg' in form:
    print '<tr><td><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr><tr><td>&nbsp;</td></tr>"
  print "<tr><td style='font-size: .8em;' colspan=2>Choose an operation <b>%s</b>:</td></tr>" % profile
  print "<tr><td style='font-size: .8em;'><a href=%s?operation=create_new_lab_form>Create New Lab</a></td></tr>" % myurl
  if os.path.exists(labcsv):
    print "<tr><td style='font-size: .8em;'><a href=%s?operation=edit_lab>View/Edit Lab Configuration</a></td></tr>" % myurl
    print "<tr><td style='font-size: .8em;'><a href=%s?operation=delete_lab>Delete Lab</a></td></tr>" % myurl
    print "<tr><td style='font-size: .8em;'><a href=%s?operation=update_guids>Update Available Lab GUIDs</a></td></tr>" % myurl
    print "<tr><td style='font-size: .8em;'><a href=%s?operation=choose_lab>View Lab GUID Utilization</a></td></tr>" % myurl
  print '</table></center>'
  printfooter(operation)
elif operation == "create_new_lab_form":
  printheader()
  printform('create_new_lab')
  printfooter()
  exit()
elif operation == "choose_lab" or operation == "edit_lab" or operation == "delete_lab" or operation == "update_guids":
  printheader()
  print "<center><table>"
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
    op = "<b>update GUIDs for</b>"
    op2 = "updatelc"
  print '<tr><td><p style="color: black; font-size: .8em;">Please choose the lab code you wish to %s:</p></td></tr>' % op
  print '<tr><td><form method="post" action="%s?operation=%s">' % (myurl, op2)
  print "<table border=0><tr><td style='font-size: .8em;'><b>Lab Code:</b></td><td><select name='labcode'>"
  with open(labcsv) as csvfile:
    labcodes = csv.DictReader(csvfile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      print('<option value="{0}">{0} - {1}</option>'.format(row['code'],row['description']))
  print "</select></td></tr>"
  print '<tr><td align=right>'
  printback2()
  print '</td><td colspan=2 align=left><input type="submit" value="Next&nbsp;>"></td></tr></table>'
  print "</form></td></tr>"
  print '</table></center>'
  printfooter(operation)
elif operation == "create_lab" or operation == 'create_new_lab':
  if 'labcode' not in form or 'labname' not in form or 'labkey' not in form:
    printheader()
    print "ERROR, please fill out required fields."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  if not os.path.exists(labcsv):
    with open(labcsv, "w") as conffile:
      conffile.write("code,description,activationkey,bastion,labguide,urls,blueprint\n")
  else:
    with open(labcsv) as conffile:
      labcodes = csv.DictReader(conffile)
      for row in labcodes:
        if row['code'] == labCode:
          printheader()
          print "ERROR, Lab %s already defined.  Delete it first." % labCode
          printfooter()
          exit()
  labName = form.getvalue('labname')
  labKey = form.getvalue('labkey')
  bastion = form.getvalue('bastion')
  docURL = form.getvalue('docurl')
  labURLS = form.getvalue('laburls')
  ln = '"%s","%s","%s","%s","%s","%s",""\n' % (labCode, labName, labKey, bastion, docURL, labURLS)
  with open(labcsv, "a") as conffile:
    conffile.write(ln)
  msg=urllib.quote("Lab Created")
  redirectURL="%s?msg=%s" % (myurl, msg)
  printheader(True, redirectURL, "0", "none")
  exit()
elif operation == "checklc" or operation == "dellc" or operation == "editlc" or operation == "updatelc":
  if 'labcode' not in form:
    printheader()
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  valid = False
  with open(labcsv) as csvfile:
    labcodes = csv.DictReader(csvfile)
    for row in labcodes:
      if row['code'] == labCode:
        valid = True
        break
  if valid == False:
    printheader()
    print "ERROR, The lab code provided not match a valid lab code."
    printback()
    printfooter()
    exit()
  if operation == "checklc":
    op = "view_lab"
  elif operation == "dellc":
    op = "del_lab"
  elif operation == "editlc":
    op = "print_lab"
  elif operation == "updatelc":
    op = "get_guids"
    printheader()
    print "<center><table>"
    print '<tr><td colspan=2 align=center><p style="color: black; font-size: 0.6em;">Please enter the catalog name and catalog item for lab code <b>%s</b> as they appear in CloudForms (Space and case sensitive):</p></td></tr>' % labCode
    print '<tr><td><form method="post" action="%s?operation=%s">' % (myurl, op)
    print "<table border=0>"
    print "<input type='hidden' name='labcode' value='%s'>" % labCode
    print "<tr><td align=right style='font-size: 0.6em;'><b>Catalog Name*:</b></td><td><input type='text' name='catname' size='20'></td></tr>"
    print "<tr><td align=right style='font-size: 0.6em;'><b>Catalog Item*:</b></td><td><input type='text' name='catitem' size='20'></td></tr>"
    print '<tr><td align=right>'
    printback2()
    print '</td>'
    print '<td align=left><input type="submit" value="Next&nbsp;>"></td></tr></table>'
    print "</form></td></tr>"
    print '</table></center>'
    exit()
  redirectURL = "%s?operation=%s&labcode=%s" % (myurl, op, labCode)
  printheader(True, redirectURL, "0")
  printfooter()
  exit()
elif operation == "print_lab":
  if 'labcode' not in form:
    printheader()
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  with open(labcsv) as csvfile:
    labcodes = csv.DictReader(csvfile)
    for row in labcodes:
      if row['code'] == labCode:
        printheader()
        printform('update_lab', row['code'], row['description'], row['activationkey'], row['bastion'], row['labguide'], row['urls'])
        printfooter()
        exit()
  printheader()
  print "ERROR, labcode %s not found." % labCode
  printfooter()
  exit()
elif operation == "view_lab" or operation == "del_lab" or operation == "update_lab":
  if 'labcode' not in form:
    printheader()
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  if operation == "del_lab" or operation == "update_lab":
    f = open(labcsv)
    old = f.readlines()
    f.close()
    with open(labcsv, "w") as conffile:
      conffile.write("code,description,activationkey,bastion,labguide,urls,blueprint\n")
    f = open(labcsv,"a")
    labcodes = csv.DictReader(old)
    if operation == "del_lab":
      for row in labcodes:
        if row['code'] != labCode:
          out = '"%s","%s","%s","%s","%s","%s",""\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['labguide'], row['urls'])
          f.write(out)
    elif operation == "update_lab":
      for row in labcodes:
        if row['code'] == labCode:
          labName = form.getvalue('labname')
          labKey = form.getvalue('labkey')
          bastion = form.getvalue('bastion')
          docURL = form.getvalue('docurl')
          labURLS = form.getvalue('laburls')
          out = '"%s","%s","%s","%s","%s","%s",""\n' % (labCode, labName, labKey, bastion, docURL, labURLS)
        else:
          out = '"%s","%s","%s","%s","%s","%s",""\n' % (row['code'], row['description'], row['activationkey'], row['bastion'], row['labguide'], row['urls'])
        f.write(out)
    f.close()
    redirectURL = "%s?operation=none" % (myurl)
    printheader(True, redirectURL, "0")
    printfooter()
    exit()
  printheader()
  asg = 0
  tot = 0
  rowc = 0
  maxrow = 10
  print "<center><table border=1 style='border-collapse: collapse;'>"
  allguidscsv = ggetc + profile + "-availableguids-" + labCode + ".csv"
  assignedcsv = ggetc + profile + "-assignedguids-" + labCode + ".csv"
  if not os.path.exists(allguidscsv):
    msg=urllib.quote("ERROR, No guids for lab code <b>{0}</b> exist.".format(labCode))
    redirectURL="%s?msg=%s" % (myurl, msg)
    printheader(True, redirectURL, "0", operation)
    exit()
  with open(allguidscsv) as allfile:
    allf = csv.DictReader(allfile)
    for allrow in allf:
      tot = tot + 1
      if rowc == 0:
        print "<tr>"
      print "<td>"
      print "<table border=0>"
      guid = allrow['guid']
      appID = allrow['appid']
      print "<tr><td style='font-size: 0.6em;'><b>" + guid + "</b></td></tr>"
      ravurl = "https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid, appID)
      print "<tr><td style='font-size: 0.6em;'><a href='%s' target='_blank'>Lab Dashboard</a></td></tr>" % ravurl
      assigned = False
      with open(assignedcsv) as ipfile:
        iplocks = csv.DictReader(ipfile)
        for row in iplocks:
          if row['guid'] == guid:
            foundGuid = row['guid']
            assigned = True
            asg = asg + 1
            ipaddr = row['ipaddr']
            #print '<tr><td><a href="vnc://%s">Remote Desktop</a></td></tr>' % ipaddr
            break
      if assigned:  
        print "<tr><td style='font-size: 0.6em; color: green;'>Assigned</td></tr>"
      else:
        print "<tr><td style='font-size: 0.6em; color: red;'>Not Assigned</td></tr>"
      print "</table>"
      print "</td>"
      rowc = rowc + 1
      if rowc == maxrow:
        print "</tr>"
        rowc = 0
  print "</table>"
  print "<table>"
  print "<tr><th style='font-size: 0.6em;'>Total Labs:</th><td style='font-size: 0.6em;'>%s</td>" % tot
  print "<th style='font-size: 0.6em;'>Assigned Labs:</th><td style='font-size: 0.6em;'>%s</td>" % asg
  avl = tot - asg
  print "<th style='font-size: 0.6em;'>Available Labs:</th><td style='font-size: 0.6em;'>%s</td></tr>" % avl
  print "<tr><td align=right>"
  printback()
  print "</td><td align=left><button onclick=\"history.go(0)\" type=button>Refresh</button></td></tr>"
  print "</table></center>"
  printfooter(operation)
elif operation == "get_guids":
  if 'labcode' not in form or 'catname' not in form or 'catitem' not in form:
    printheader()
    print "ERROR, no labcode, catname, and/or catitem provided."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  catName = form.getvalue('catname')
  catItem = form.getvalue('catitem')
  allguidscsv = ggetc + profile + "-availableguids-" + labCode + ".csv"
  getguids = ggbin + "/getguids.py"
  config = ConfigParser.ConfigParser()
  config.read(cfgfile)
  cfurl = config.get('guidgrabber', 'cfurl')
  cfuser = config.get('guidgrabber', 'cfuser')
  cfpass = config.get('guidgrabber', 'cfpass')
  ret = call([getguids, "--cfurl", cfurl, "--cfuser", cfuser, "--cfpass", cfpass, "--catalog", catName, "--item", catItem, "--out", allguidscsv])
  printheader()
  if ret == 0:
    print "Success! GUIDs updated."
  else:
    print "ERROR, no updating GUIDs failed."
  printback2()
  printfooter()
  exit()
else:
  printheader()
  print "ERROR, invalid operation."
  printback()
  printfooter()
  exit()
