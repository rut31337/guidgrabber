#!/usr/bin/python

import csv
import cgi
import urllib
import os

ggetc = "/var/www/guidgrabber/etc/"
labcsv = ggetc + "labconfig.csv"
myurl = "/guidgrabber/manager.cgi"

def printback():
  print '<br><button onclick="goBack()">< Go Back</button>'

def callredirect(redirectURL, waittime=0):
  print '<head>'
  print '<meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL)
  print '</head><html><body></body></html>'

def includehtml(fname):
  with open(fname, 'r') as fin:
    print fin.read()

def printheader(operation="requestguid"):
  print "Content-type:text/html\r\n\r\n"
  print '<html><head>'
  if operation == "manage":
    waittime = 30
    redirectURL = "/guidgrabber/manager.cgi?operation=manage&labcode=%s" % labCode
    print '<meta http-equiv="refresh" content="%s;url=%s" />' % (waittime, redirectURL)
    includehtml('head_mgr.inc')
  elif operation == "showguid":
    includehtml('head_mgr.inc')
  else:
    includehtml('head_mgr.inc')
  print '</head>'
  if operation == "showguid":
    includehtml('topbar2.inc')
    includehtml('textarea_mgr.inc')
  else:
    includehtml('topbar.inc')
    includehtml('textarea_mgr.inc')

def printfooter(operation="requestguid"):
  if operation == "showguid":
    includehtml('footer2.inc')
  else:
    includehtml('footer.inc')
  print '</body>'
  print '</html>'
  exit()

form = cgi.FieldStorage()
if 'operation' in form:
  operation = form.getvalue('operation')
else:
  operation = "requestguid"

if operation == "requestguid":
  printheader()
  print "<center><table>"
  if 'msg' in form:
    print '<tr><td><p style="color: black; font-size: 1.2em;">' + form.getvalue('msg') + "</p></td></tr>"
  print '<tr><td><p style="color: black; font-size: 1.2em;">Please choose the lab code you wish to manage:</p></td></tr>'
  print "<tr><td><form method='post' action='/guidgrabber/manager.cgi?operation=checklc'>"
  print "<table border=0><tr><td><b>Lab Code:</b></td><td><select name='labcode'>"
  with open(labcsv) as csvfile:
    labcodes = csv.DictReader(csvfile)
    for row in labcodes:
      if row['code'].startswith("#"):
        continue
      print('<option value="{0}">{0} - {1}</option>'.format(row['code'],row['description']))
  print "</select></td></tr>"
  print '<tr><td colspan=2 align=center><input type="submit" value="Next&nbsp;>"></td></tr></table>'
  print "</form></td></tr>"
  print '</table></center>'
  printfooter(operation)
if operation == "checklc":
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
  printheader()
  redirectURL = "/guidgrabber/manager.cgi?operation=manage&labcode=%s" % labCode
  callredirect(redirectURL, waittime=0)
  printfooter()
  exit()
if operation == "manage":
  if 'labcode' not in form:
    printheader()
    print "ERROR, no labcode provided."
    printback()
    printfooter()
    exit()
  labCode = form.getvalue('labcode')
  printheader(operation)
  asg = 0
  tot = 0
  rowc = 0
  maxrow = 10
  print "<center><table border=1>"

  allguidscsv = ggetc + "availableguids-" + labCode + ".csv"
  assignedcsv = ggetc + "assignedguids-" + labCode + ".csv"
  if not os.path.exists(allguidscsv):
    msg=urllib.quote("ERROR, No guids for lab code <b>{0}</b> exist.".format(labCode))
    redirectURL="%s?msg=%s" % (myurl,msg)
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
      print "<tr><td>" + guid + "</td></tr>"
      ravurl = "https://www.opentlc.com/cgi-bin/dashboard.cgi?guid=%s&appid=%s" % (guid, appID)
      print "<tr><td><a href='%s' target='_blank'>Lab Dashboard</a></td></tr>" % ravurl
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
        print "<tr><td>Assigned</td></tr>"
      else:
        print "<tr><td>Not Assigned</td></tr>"
      print "</table>"
      print "</td>"
      rowc = rowc + 1
      if rowc == maxrow:
        print "</tr>"
        rowc = 0
  print "</table>"
  print "<table>"
  print "<tr><th>Total Labs:</th><td>%s</td></tr>" % tot
  print "<tr><th>Assigned Labs:</th><td>%s</td></tr>" % asg
  print "</table></center>"
  print "<br><center><a href='javascript:history.go(0)'>[Refresh]</a></center>"
  printfooter(operation)
