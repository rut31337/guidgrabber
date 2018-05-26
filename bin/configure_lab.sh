#!/bin/bash

echo "Create Lab Config? (y/N): ";read yn
if [ "$yn" == "y" ]
then
  echo -n "Enter a Profile Name (ex. OPENTLC Login): ";read profile
  labconfig="/var/www/guidgrabber/etc/${profile}-labconfig.csv"
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
  if [ ! -f $labconfig ]
  then
    echo "code,description,activationkey,bastion,labguide,urls,blueprint" > $labconfig
  fi
  echo "${labcode},${labdesc},${labkey},${bastion},${docurl},${laburls}," >> $labconfig
  echo "You can edit /var/www/guidgrabber/etc/${profile}-labconfig.csv later to change/add more info not entered here.  See documentation."
else
  echo -n "Enter a Profile Name (ex. OPENTLC Login): ";read profile
  echo -n "Enter Lab Code defined in labconfig.csv (ex. LXXXX).  Please, no spaces or special characters: ";read labcode
  echo "Make sure you set up /var/www/guidgrabber/etc/${profile}-labconfig.csv manually with an entry for lab code ${labcode}.  See profile-labconfig-labcode.csv for more info."
fi

echo -n "Enter CF User: ";read user
echo -n "Enter CF Pass: ";stty -echo;read pass;stty echo
echo
echo -n "Enter Catalog Name: ";read cat
echo -n "Enter Item Name: ";read item
/var/www/guidgrabber/bin/getguids.py --cfurl https://rhpds.redhat.com --cfuser $user --cfpass $pass --catalog "$cat" --item "$item" --out /var/www/guidgrabber/etc/${profile}-availableguids-${labcode}.csv

echo;echo "If you need to update your list of available guids you can safely run this command again as much as needed:"
echo "/var/www/guidgrabber/bin/getguids.py --cfurl https://rhpds.redhat.com --cfuser $user --cfpass $pass --catalog \"$cat\" --item \"$item\" --out /var/www/guidgrabber/etc/${profile}-availableguids-${labcode}.csv"
