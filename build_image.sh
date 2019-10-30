#!/bin/bash

DEFAULT_IMAGE_NAME="sconecuratedimages/issre2019:radiomics-asperathos"
DEFAULT_CONFIG_JSON="config.json"

IMAGE_NAME=$1
CONFIG_JSON=$2

if [ -z ${IMAGE_NAME} ]; then
    IMAGE_NAME=${DEFAULT_IMAGE_NAME}
    echo -e "[WARNING] Image name is not set. Falling back to '${IMAGE_NAME}'...\n"
else
    if [ ${IMAGE_NAME} == "--help" -o ${IMAGE_NAME} == "-h" ]; then
        echo "usage: $0 <image name> <configuration json output>"
        exit 0
    fi
fi

if [ -z ${CONFIG_JSON} ]; then
    CONFIG_JSON=${DEFAULT_CONFIG_JSON}
    echo -e "[WARNING] Configuration JSON is not set. Falling back to '${CONFIG_JSON}'...\n"
else
    if [ ${CONFIG_JSON} == "--help" -o ${CONFIG_JSON} == "-h" ]; then
        echo "usage: $0 <image name> <configuration json output>"
        exit 0
    fi
fi


# Build image and get FSPF tag & key
OUTPUT_FILE=$(mktemp)
echo -e "\n[INFO] Building '${IMAGE_NAME}' image...\n"
docker build --build-arg DATETIME=$(date +%s) -t ${IMAGE_NAME} . 2>&1 | tee ${OUTPUT_FILE}
FSPF_OUTPUT=`cat ${OUTPUT_FILE} | grep "Encrypted file system protection file"`
rm ${OUTPUT_FILE}

FSPF_TAG=`echo ${FSPF_OUTPUT} | cut -d' ' -f9`
FSPF_KEY=`echo ${FSPF_OUTPUT} | cut -d' ' -f11`

# Get MRENCLAVE from Python
MRENCLAVE=`docker run --rm --env-file scone-env.list ${IMAGE_NAME} python -c 'exit()' 2>&1 | grep "Enclave hash:" | cut -d' ' -f3`

echo "[INFO] Writing '${CONFIG_JSON}'..."
cat << EOF | tee ${CONFIG_JSON}
{
	"mrenclave": "${MRENCLAVE}",
	"image-name": "${IMAGE_NAME}",
	"fspf-tag": "${FSPF_TAG}",
	"fspf-key": "${FSPF_KEY}",
	"fspf-path": "/fspf.pb"
}
EOF

echo "[INFO] Done! Now, push built image to a Docker Registry and use 'submit-data.py' to create a job."
