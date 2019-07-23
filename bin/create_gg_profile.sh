#!/bin/bash

usage() {
  echo "Usage: $0 -p <profile> -l <lab code> -d <description> -a <activation key> -c <catalog name> -i <catalog item> -g <GUID> [ -b <bastion> -D <doc url> -u <urls> -U <lab user> -s <ssh key> -e <environment> -B <blueprint> -x <shared user count> -w <infra workload> -r <region> -C <city> -f <sales force ID> -S <survey link> -E <env size> -W <student workload> -m <bare metal> -t <service type>]"
  echo
  echo "To also create available GUIDs add -I where -g <guid> is required with optional -y <sandbox domain>"
  echo "If -t is set to agnosticd-shared you must set -x to an integer that equals the number of shared users to generate."
}

while getopts Ip:l:d:a:c:i:b:D:u:U:s:e:B:x:C:w:r:C:f:S:E:W:m:t:g:y: FLAG; do
  case $FLAG in
    p) profile="${OPTARG}";;
    l) labCode="${OPTARG}";;
    d) description="${OPTARG}";;
    a) actKey="${OPTARG}";;
    c) catalogName="${OPTARG}";;
    i) catalogItem="${OPTARG}";;
    b) bastion="${OPTARG:-None}";;
    D) docURL="${OPTARG:-None}";;
    u) URLS="${OPTARG:-None}";;
    U) labUser="${OPTARG:-None}";;
    s) sshKey="${OPTARG:-None}";;
    e) environment="${OPTARG:-None}";;
    B) blueprint="${OPTARG:-None}";;
    x) sharedUsers="${OPTARG:-None}";;
    w) infraWorkload="${OPTARG:-None}";;
    r) region="${OPTARG:-None}";;
    C) city="${OPTARG:-None}";;
    f) salesforce="${OPTARG:-None}";;
    S) surveyLink="${OPTARG:-None}";;
    E) envSize="${OPTARG:-None}";;
    W) studentWorkload="${OPTARG:-None}";;
    m) bareMetal="${OPTARG:-None}";;
    t) serviceType="${OPTARG:-None}";;
    g) GUID="${OPTARG}";;
    y) sandboxDomain="${OPTARG}";;
    I) createAvailable=true;;
    *) usage;exit;;
  esac
done

if [ -z "$profile" -o -z "$labCode" -o -z "$description" -o -z "$actKey" -o -z "$catalogName" -o -z "$catalogItem" ]
then
  echo "ERROR: Lab Code, Description, Activation Key, Catalog Name, and Catalog Item are REQUIRED fields."
  echo
  usage
  exit 1
fi

if [ "$createAvailable" -a -z "$GUID" ]
then
  echo "ERROR: GUID is REQUIRED when using -I."
  echo
  usage
  exit 1
fi

if [ $createAvailable ]
then
  if [ "$serviceType" != "agnosticd-shared" ]
  then
    echo "ERROR: Create available flag set but service type is not agnosticd-shared.  This is an unsupported configuration at this time."
    echo
    usage
    exit 1
  fi
fi

if [ "$serviceType" == "agnosticd-shared" ]
then
  if [ -z "$sharedUsers" ]
  then
    echo "ERROR: Service Type is agnosticd-shared but -x does not specify the number of shared users."
    echo
    usage
    exit 1
  fi
  if [[ ! $sharedUsers =~ ^[0-9]+$ ]]
  then
    echo "ERROR: -x must be a positive integer value."
    echo
    usage
    exit 1
  fi
fi

profileDir="/var/www/guidgrabber/etc/${profile}"

if [ ! -d $profileDir ]
then
  mkdir -p $profileDir
fi

labConfig="${profileDir}/labconfig.csv"

if [ ! -f $labConfig ]
then
  echo "code,description,activationkey,bastion,docurl,urls,catname,catitem,labuser,labsshkey,environment,blueprint,shared,infraworkload,region,city,salesforce,surveylink,envsize,studentworkload,baremetal,servicetype" > $labConfig
else
  sed -i "/\"$labCode\",/d" $labConfig
fi

echo "\"$labCode\",\"$description\",\"$actKey\",\"$bastion\",\"$docURL\",\"$URLS\",\"$catalogName\",\"$catalogItem\",\"$labUser\",\"$sshKey\",\"$environment\",\"$blueprint\",\"$sharedUsers\",\"$infraWorkload\",\"$region\",\"$city\",\"$salesforce\",\"$surveyLink\",\"$envSize\",\"$studentWorkload\",\"$bareMetal\",\"$serviceType\"" >> $labConfig

if [ "$createAvailable" ]
then
  availableFile="${profileDir}/availableguids-${labCode}.csv"
  if [ "$serviceType" == "agnosticd-shared" ]
  then
    echo "guid,appid,servicetype,sandboxzone" > $availableFile
    x=1
    while [ $x -le $sharedUsers ]
    do
      echo "${x},,shared," >> $availableFile
      ((x=$x+1))
    done
  fi
fi

chown -R apache:apache $profileDir
/sbin/restorecon -R $profileDir
