#!/bin/bash

if [ -z $1 ]; then
	OUTPUT="client.pem"
else
	if [ $1 == "--help" ]; then
		echo "usage: $0 <output certificate file. [default='client.pem']>"
		exit 1
	fi
	OUTPUT=$1
fi

# Generate a 4096-bit RSA certificate & key

openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
	-subj "/C=EU/ST=PALAEMON/L=CLIENT/O=Internet/CN=scontain.com" \
	-out ./.tmp-client.crt -keyout ./.tmp-client-key.key && \
cat .tmp-client.crt .tmp-client-key.key > ${OUTPUT} && \
rm .tmp-client.crt .tmp-client-key.key && \
echo -e "\n[INFO] '${OUTPUT}' written successfully."

