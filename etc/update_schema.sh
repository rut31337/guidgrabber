#!/bin/bash


for file in */labconfig.csv; do sed -i '1 s/^.*$/code,description,activationkey,bastion,docurl,urls,catname,catitem,labuser,labsshkey,environment,blueprint,shared,workload,region,city,salesforce,surveylink/' $file; done
