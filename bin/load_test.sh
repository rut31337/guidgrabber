#!/bin/bash

ak=loadtest

tmpdir=/tmp/gg_load_testing
rm -rf $tmpdir
mkdir $tmpdir

LCS=`cat /var/www/guidgrabber/etc/prutledg/labconfig.csv |cut -f1 -d,|sed 's/"//g'|grep -v '^code'`

y=10
for lc in $LCS
do
  x=1
  while [ $x -le 55 ]
  do
    curl -s -d "actkey=$ak&labcode=$lc&ipaddr=10.0.$y.$x" -X POST https://www.opentlc.com/gg/gg.cgi?operation=searchguid\&profile=prutledg |grep "guid="|cut -f6 -d=|cut -f1 -d'&' >> $tmpdir/$lc.txt &
    ((x=$x + 1))
  done
  ((y=$y + 10))
done
