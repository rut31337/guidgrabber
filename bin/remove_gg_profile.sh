#!/bin/bash

usage() {
  echo "Usage: $0 -p <profile> -l <lab code>"
  echo
}

while getopts p:l: FLAG; do
  case $FLAG in
    p) profile="${OPTARG}";;
    l) labCode="${OPTARG}";;
    *) usage;exit;;
  esac
done

if [ -z "$profile" -o -z "$labCode" ]
then
  echo "ERROR: Profile and Lab Code are REQUIRED fields."
  echo
  usage
  exit 1
fi

profileDir="/var/www/guidgrabber/etc/${profile}"

if [ ! -d $profileDir ]
then
  echo "ERROR profile dir $profileDir does not exist!"
  exit 1
fi

availableGuids="${profileDir}/availableguids-$labCode.csv"
rm -f $availableGuids

assignedGuids="${profileDir}/assignedguids-$labCode.csv"
rm -f $assignedGuids

labConfig="${profileDir}/labconfig.csv"

if [ ! -f $labConfig ]
then
  echo "ERROR profile dir $profileDir does not exist!"
  exit 1
fi

sed -i "/\"$labCode\",/d" $labConfig

