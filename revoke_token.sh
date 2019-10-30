#!/bin/bash

# This script will revoke an access token from OpenStack and create 
# a script that sets necessary variables.

exit_not_set() {
    if [ -z ${OS_AUTH_TOKEN} ]; then echo "OS_AUTH_TOKEN is unset... exiting!" && exit 1; fi
    if [ ! `which openstack` ]; then echo "python-openstackclient not found... exiting!" && exit 1; fi
}

exit_not_set

CMD_OUT=`openstack token revoke ${OS_AUTH_TOKEN} 2>&1`

if [[ -z ${CMD_OUT} ]]; then
	echo "Done!"
else
	echo ${CMD_OUT}
fi
