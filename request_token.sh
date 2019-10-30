#!/bin/bash

# This script will issue an access token from OpenStack and create 
# a script that sets necessary variables.

exit_not_set() {
    if [ -z ${OS_USER_DOMAIN_NAME} ]; then echo "OS_USER_DOMAIN_NAME is unset... exiting!" && exit 1; fi
    if [ -z ${OS_USERNAME} ]; then echo "OS_USERNAME is unset... exiting!" && exit 1; fi
    if [ -z ${OS_PASSWORD} ]; then echo "OS_PASSWORD is unset... exiting!" && exit 1; fi
    if [ -z ${OS_PROJECT_DOMAIN_ID} ]; then echo "OS_PROJECT_DOMAIN_ID is unset... exiting!" && exit 1; fi
    if [ -z ${OS_PROJECT_ID} ]; then echo "OS_PROJECT_ID is unset... exiting!" && exit 1; fi
    if [ -z ${OS_PROJECT_NAME} ]; then echo "OS_PROJECT_NAME is unset... exiting!" && exit 1; fi
    if [ ! `which openstack` ]; then echo "python-openstackclient not found... exiting!" && exit 1; fi
}

exit_not_set

TOKEN_RESPONSE=`openstack token issue -f shell --prefix os_ | grep os_id | cut -d'=' -f2 | tr -d '"'`

if [ -z ${TOKEN_RESPONSE} ]; then
	echo ${TOKEN_RESPONSE}
	echo "[ERROR] Unable to request a token from OpenStack. Exiting ..."
	exit 1
fi

OUTPUT_FILE="${OS_PROJECT_NAME}-tokenrc.sh"

echo -n "Creating ${OUTPUT_FILE} ... "

echo -e "#!/bin/bash\n\nexport OS_AUTH_URL=${OS_AUTH_URL}\nexport OS_AUTH_TOKEN=\"${TOKEN_RESPONSE}\"\nexport OS_PROJECT_NAME=\"${OS_PROJECT_NAME}\"\nexport OS_PROJECT_DOMAIN_ID=\"${OS_PROJECT_DOMAIN_ID}\"" > ${OUTPUT_FILE}

echo "Done!"
