#!/bin/bash

# This script export environment variables into files

unset SCONE_ALPINE

OUTPUT_PATH="/env"

mkdir -p ${OUTPUT_PATH}
for env in `printenv`; do
	env_name=`echo ${env} | cut -d"=" -f1`
	value=`echo ${env} | cut -d"=" -f2`
	echo ${value} > ${OUTPUT_PATH}/${env_name}
done

export SCONE_ALPINE=1
