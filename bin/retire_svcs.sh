#!/bin/bash

# CloudForms Retire Services - Patrick Rutledge prutledg@redhat.com

# Defaults
uri="https://cf.example.com"

# Dont touch from here on

usage() {
  echo "Error: Usage $0 -c <catalog name> -i <item name> -u <username> [ -f <optional-user-to-filter-to> -P <password> -w <uri> -n -N ]"
}

while getopts Nnu:P:c:i:w:f:l: FLAG; do
  case $FLAG in
    n) noni=1;;
    N) insecure=1;;
    u) userName="$OPTARG";;
    f) userFilter="$OPTARG";;
    P) password="$OPTARG";;
    c) catalogName="$OPTARG";;
    i) itemName="$OPTARG";;
    w) uri="$OPTARG";;
    l) labCode="$OPTARG";;
    *) usage;exit;;
    esac
done

if [ -z "$catalogName" -o -z "$itemName" ]
then
  usage
  exit 1
fi

if [ -z "$userName" ]
then
  echo -n "Enter CF Username: ";read userName
fi

if [ -z "$password" ]
then
  echo -n "Enter CF Password: "
  stty -echo
  read password
  stty echo
  echo
fi

if [ "$insecure" == 1 ]
then
  ssl="-k"
else
  ssl=""
fi

tok=`curl -s $ssl --user $userName:$password -X GET -H "Accept: application/json" $uri/api/auth|python -m json.tool|grep auth_token|cut -f4 -d\"`

if [ -z "$tok" ]
then
  echo "ERROR: Authentication failed to CloudForms."
  exit 1
fi

catalogName=`echo $catalogName|sed "s/ /+/g"`
catalogID=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$uri/api/service_catalogs?attributes=name,id&expand=resources&filter%5B%5D=name='$catalogName'" | python -m json.tool |grep '"id"' | cut -f2 -d:|sed "s/[ ,\"]//g"`
if [ -z "$catalogID" ]
then
  echo "ERROR: Invalid Catalog $catalogName"
  exit 1
fi
echo "catalogID is $catalogID"


itemName=`echo $itemName|sed "s/ /+/g"`
itemID=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$uri/api/service_templates?attributes=service_template_catalog_id,id,name&expand=resources&filter%5B%5D=name='$itemName'&filter%5B%5D=service_template_catalog_id='$catalogID'" | python -m json.tool |grep '"id"' | cut -f2 -d:|sed "s/[ ,\"]//g"`
if [ -z "$itemID" ]
then
  echo "ERROR: Invalid Catalog item $itemName"
  exit 1
fi
echo "itemID is $itemID"

if [ -n "$userFilter" ]
then
  uif=$userFilter
else
  uif=$userName
fi

userid=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$uri/api/users?expand=resources&attributes=id&filter%5B%5D=userid='$uif'"| python -m json.tool | grep '"id"' | cut -f2 -d:|sed "s/[ ,\"]//g"`

svcs=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$uri/api/services?attributes=href&expand=resources&filter%5B%5D=evm_owner_id='$userid'&filter%5B%5D=service_template_id='$itemID'" | python -m json.tool |grep '"href"'|grep "services/"|cut -f2- -d:|sed -e "s/[ ,\"]//g"`

if [ "$noni" != 1 ]
then
  echo -n "Are you sure you wish to retire/delete ALL services deployed from this catalog item? (y/N): ";read yn
  if [ "$yn" != "y" ]
  then
    echo "Exiting."
    exit
  fi
fi

PAYLOAD="{ \"action\": \"retire\" }"
if [ -n "$labCode" ]
then
  echo "Deleting services with lab code: $labCode"
fi

echo -n "Retiring Services"
for svc in $svcs
do
  if [ -n "$labCode" ]
  then
    for ca in `curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$svc?attributes=custom_attributes&expand=resources&filter%5B%5D=evm_owner_id='$userid'&filter%5B%5D=service_template_id='$itemID'"| jq '.custom_attributes[]'| jq -r '"\(.name),\(.value)"'`
    do
      k=`echo $ca|cut -f1 -d,`
      if [ $k == "labCode" ]
      then
        v=`echo $ca|cut -f2 -d,`
        if [ "$v" == $labCode ]
        then
          output=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X POST $svc -d "$PAYLOAD"`
          break
        fi
      fi
    done
  else
    output=`curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X POST $svc -d "$PAYLOAD"`
  fi
  echo -n "."
  sleep 1
done
echo
