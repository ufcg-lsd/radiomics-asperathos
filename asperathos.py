import json
import os
import requests


def get_template():
    curr_path = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(curr_path, "asperathos-default.json")

    return json.load(open(template_file, 'r'))


def submit_job(config, publish_url):
    r = requests.post(publish_url, json=config, verify=False)

    return (r.status_code, r.text)


def get_job_info(job_id, publish_url):
    r = requests.get("%s/%s" % (publish_url, job_id), publish_url, verify=False)

    return r.text