#!/bin/bash

# CloudForms Get Services - Patrick Rutledge prutledg@redhat.com

# Defaults
uri="https://cf.example.com"

# Dont touch from here on

usage() {
  echo "Error: Usage $0 -u <username> [ -P <password> -w <uri> -N ]"
}

while getopts Nu:w:P: FLAG; do
  case $FLAG in
    u) username="$OPTARG";;
    P) password="$OPTARG";;
    N) insecure=1;;
    w) uri="$OPTARG";;
    *) usage;exit;;
    esac
done

if [ -z "$username" ]
then
  echo -n "Enter CF Username: ";read username
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

tok=`curl -s $ssl --user $username:$password -X GET -H "Accept: application/json" $uri/api/auth|python -m json.tool|grep auth_token|cut -f4 -d\"`

curl -s $ssl -H "X-Auth-Token: $tok" -H "Content-Type: application/json" -X GET "$uri/api/services?attributes=name&expand=resources" | python -m json.tool | grep '"name"'|cut -f2 -d:|sed -e "s/[ \"]//g" |sort|egrep -v "services,$|retire$|query$|assign"
