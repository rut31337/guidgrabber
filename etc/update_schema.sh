#!/bin/bash


for file in */labconfig.csv; do sed -i '1 s/^.*$/code,description,activationkey,bastion,docurl,urls,catname,catitem,labuser,labsshkey,environment,blueprint,shared,infraworkload,region,city,salesforce,surveylink,envsize,studentworkload,baremetal,servicetype/' $file; done
