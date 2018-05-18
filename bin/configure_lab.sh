#!/bin/bash

echo "Create Lab Config? (y/N): ";read yn
if [ "$yn" == "y" ]
then
  echo -n "Enter Lab Description: ";read labdesc
  echo -n "Enter Lab Code (ex. LXXXX) no spaces or special characters: ";read labcode
  echo -n "Enter Lab Key: ";read labkey
  echo -n "Enter Lab Bastion FQDN [bastion-REPL.rhpds.opentlc.com]: ";read bastion
  if [ -z "$bastion" ]
  then
    bastion="bastion-REPL.rhpds.opentlc.com"
  fi
  echo -n "Enter Lab Doc URL: ";read docurl
  echo -n "Enter Semicolon Delimited List of Lab URLs (ex. https://www-REPL.rhpds.opentlc.com): ";read laburls
  if [ ! -f /var/www/guidgrabber/etc/labconfig.csv ]
  then
    echo "code,description,activationkey,bastion,labguide,urls,blueprint" > /var/www/guidgrabber/etc/labconfig.csv
  fi
  echo "${labcode},${labdesc},${labkey},${bastion},${docurl},${laburls}," >> /var/www/guidgrabber/etc/labconfig.csv
else
  echo -n "Enter Lab Code defined in labconfig.csv (ex. LXXXX).  Please, no spaces or special characters: ";read labcode
  echo "Make sure you set up /var/www/guidgrabber/etc/labconfig.csv manually with an entry for lab code ${labcode}.  See labconfig.example.csv for more info."
fi

echo -n "Enter CF User: ";read user
echo -n "Enter CF Pass: ";stty -echo;read pass;stty echo
echo
echo -n "Enter Catalog Name: ";read cat
echo -n "Enter Item Name: ";read item
/var/www/guidgrabber/bin/getguids.py --cfurl https://rhpds.redhat.com --cfuser $user --cfpass $pass --catalog "$cat" --item "$item" --out /var/www/guidgrabber/etc/availableguids-${labcode}.csv
