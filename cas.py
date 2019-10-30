import os
import re
import requests
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION_TEMPLATE = """
name: ${SESSION_NAME}
digest: create
predecessor: null

services:
  - name: ${APPLICATION_NAME}
    image_name: ${IMAGE_NAME}
    mrenclaves: [${MR_ENCLAVE}]
    command: python2.7 -B anonymise.py -o /mnt/output/images
    pwd: /app
    environment:
      ENCRYPTION_KEY: "${ENCRYPTION_KEY}"
      ITEM_LEASE_SECS: "${ITEM_LEASE_SECS}"
      OS_AUTH_URL: "${OS_AUTH_URL}"
      OS_AUTH_TOKEN: "${OS_AUTH_TOKEN}"
      OS_PROJECT_NAME: "${OS_PROJECT_NAME}"
      OS_PROJECT_DOMAIN_ID: "${OS_PROJECT_DOMAIN_ID}"

    tags: [default]
    fspf_tag: ${IMAGE_FSPF_TAG}
    fspf_key: ${IMAGE_FSPF_KEY}
    fspf_path: ${IMAGE_FSPF_PATH}

images:
  - name: ${IMAGE_NAME}
    mrenclaves: [${MR_ENCLAVE}]
    tags: [default]
"""

def get_config_id(session_id, application_name):
    return "%s/%s" % (session_id, application_name)


def get_attestation_address(cas_address):
    cas_address = check_cas_address(cas_address)
    return ("%s:%d" % (cas_address[0], int(cas_address[2])))


def check_cas_status(cas_address, cert_path):
    cas_address = check_cas_address(cas_address)
    cas_rest = "https://%s:%d/session" % (cas_address[0], int(cas_address[1]))

    try:
        r = requests.get(cas_rest, cert=cert_path, verify=False)

        assert r.status_code in [400, 404]
    except:
        print("[ERROR] Unable to connect to CAS! Exiting...")
        exit(1)


def check_cas_address(cas_address):
    regex = r'(.*):([0-9]+):([0-9]+)'
    pattern = re.compile(regex)

    re_match = re.match(pattern, cas_address)
    if re_match is not None:
        return re_match.groups()

    return False


def get_session_content(session_name, application_name, image_name, mr_enclave,
                        image_fspf_tag, image_fspf_key, image_fspf_path, aes_key,
                        lease_secs):
    assert len(mr_enclave) == 64
    lease_secs = str(int(lease_secs)) # ensure that lease_secs type is integer

    session = SESSION_TEMPLATE
    session = session.replace("${SESSION_NAME}", session_name)
    session = session.replace("${APPLICATION_NAME}", application_name)
    session = session.replace("${IMAGE_NAME}", image_name)
    session = session.replace("${MR_ENCLAVE}", mr_enclave)
    session = session.replace("${IMAGE_FSPF_TAG}", image_fspf_tag)
    session = session.replace("${IMAGE_FSPF_KEY}", image_fspf_key)
    session = session.replace("${IMAGE_FSPF_PATH}", image_fspf_path)
    session = session.replace("${ENCRYPTION_KEY}", aes_key)
    session = session.replace("${ITEM_LEASE_SECS}", lease_secs)
    session = session.replace("${OS_AUTH_URL}", os.environ["OS_AUTH_URL"])
    session = session.replace("${OS_AUTH_TOKEN}", os.environ["OS_AUTH_TOKEN"])
    session = session.replace("${OS_PROJECT_NAME}", os.environ["OS_PROJECT_NAME"])
    session = session.replace("${OS_PROJECT_DOMAIN_ID}", os.environ["OS_PROJECT_DOMAIN_ID"])

    return session


def post_session(cas_address, cert_path, session_name, application_name, image_name,
                 mr_enclave, image_fspf_tag, image_fspf_key, image_fspf_path, aes_key,
                 lease_secs):
    session_data = get_session_content(session_name, application_name, image_name,
                                       mr_enclave, image_fspf_tag, image_fspf_key,
                                       image_fspf_path, aes_key, lease_secs)
    cas_address = check_cas_address(cas_address)
    cas_rest = "https://%s:%d/session" % (cas_address[0], int(cas_address[1]))

    r = requests.post(cas_rest, data=session_data,
                      cert=cert_path, verify=False)

    if r.status_code == 200 or r.status_code == 201:  # HTTP OK
        print(r.text)
        return True

    return False
