#!/bin/bash


#bold=$(tput bold)
#blink="$bold$(tput smul)"
#normal="\033[0m"
bold=""
blink=""
normal=""

for dir in rhtemgr napc
do

cd /var/www/guidgrabber/etc/$dir

echo
echo "               GUID WATCH $dir"
echo
printf "%-10s | %-10s | %-10s\n" "LAB CODE" "AVAILABLE" "ASSIGNED"
files=`ls available*.csv 2>/dev/null`
if [ $? -ne 0 ]
then
  exit
fi

for file in $files
do
num=`wc -l $file|cut -f1 -d' '`
((av=$num-1))
lc=`echo $file|cut -f2,3 -d'-'|sed 's/.csv//'`
af="assignedguids-${lc}.csv"
if [ -f $af ]
then
  num=`wc -l $af|cut -f1 -d' '`
  ((as=$num-1))
else
  as=0
fi

printf "${bold}%-10s${normal} | ${bold}%-10s${normal} | ${bold}%-10s${normal}\n" "$lc" "$av" "$as"
done

done
