# ISSRE '19 - Building Applications for Trustworthy Data Analysis in the Cloud

This application is a use case from the EU-Brazil Atmosphere project. For more information on the project, visit our website at [https://www.atmosphere-eubrazil.eu/](https://www.atmosphere-eubrazil.eu/). The original application is hosted at the project's GitHub repository at [https://github.com/eubr-atmosphere/radiomics](https://github.com/eubr-atmosphere/radiomics). More details about SCONE can also be found at [https://sconedocs.github.io](https://sconedocs.github.io). More details about Asperathos can also be found at [https://github.com/ufcg-lsd/asperathos](https://github.com/ufcg-lsd/asperathos).

## Radiomics Approach

This application focuses on the implementation of the pilot application on Medical Imaging Biomarkers. This radiomics approach includes a processing pipeline to extract frames from videos, classify them, select those frames with significative data, filter them and extract image features using first- and second-order texture analysis and image computing. Finally, that pipeline concludes a classification (normal, definite or borderline RHD). 

## Running as Asperathos Job

### Requirements

* Docker v19.03.2 (optional - required for step 3)
* OpenSSL v1.0.2g
* Python v3.5.2
* pip v12.2.3
* Python libraries (use of virtualenv is recommended): 
  * cryptography==2.7
  * python-keystoneclient==3.21.0
  * python-openstackclient==4.0.0
  * python-swiftclient==3.8.1
  * requests==2.22.0
* A running instance of Palaemon
* SGX-Enabled Kubernetes cluster
  * Each worker node must run a SCONE-LAS instance
* OpenStack OpenRC script

Note: the deployment could be done using different versions of requirements listed above.

### Setup a Virtual Environment

Python virtual environments (aka virtualenv) allows the user to install Python packages into an isolated environment.

```bash
$ python3 -m virtualenv -p /usr/bin/python3 .virtual-env
Already using interpreter /usr/bin/python3
Using base prefix '/usr'
New python executable in /home/ffosilva/radiomics/asperathos/.virtual-env/bin/python3
Also creating executable in /home/ffosilva/radiomics/asperathos/.virtual-env/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.

$ source .virtual-env/bin/activate
$ pip install -r requirements.txt
```

### Step 1: Issue a OpenStack token

Note: the name of \*rc.sh scripts must change according to the OpenStack project name.

```bash
$ source issre-tutorial-openrc.sh
Please enter your OpenStack Password for project asperathos as user fabiosilva:
<type the OpenStack password>
$ ./request_token.sh
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 10250  100  9586  100   664  24146   1672 --:--:-- --:--:-- --:--:-- 25818
Creating issre-tutorial-tokenrc.sh ... Done!
$ source issre-tutorial-tokenrc.sh
```

### Step 2: Generate Palaemon API client cert & key

```bash
$ ./generate_certificate.sh
Generating a RSA private key
....................................................................++++
.........................................................................................................................................................................................................................++++
writing new private key to './.tmp-client-key.key'
-----

[INFO] 'client.pem' written successfully.
```

### Step 3: Build the Docker image

If there's a provided pre-built image, skip this step. To build, execute the following command:

```bash
# NOTE: image building process takes around 30 minutes

$ ./build_image.sh lsd-registry.duckdns.org:5000/issre2019/radiomics-asperathos:latest

[INFO] Building 'lsd-registry.duckdns.org:5000/issre2019/radiomics-asperathos:latest' image...

Sending build context to Docker daemon  185.6MB
Step 1/26 : FROM sconecuratedimages/datasystems:tensorscone as tensorscone
 ---> 83847162d638

...

Successfully built 77752eee18ba
Successfully tagged lsd-registry.duckdns.org:5000/issre2019/radiomics-asperathos:latest
[INFO] Writing 'config.json'...
{
    "mrenclave": "5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d",
    "image-name": "lsd-registry.duckdns.org:5000/issre2019/radiomics-asperathos:latest",
    "fspf-tag": "d2bd156761ba32ede882b44228015e12",
    "fspf-key": "4b242a13d64ba02eaa53f903b3a9d30225227a05e96580ff82389a00b1ab8e1f",
    "fspf-path": "/fspf.pb"
}
[INFO] Done! Now, push built image to a Docker Registry and use 'submit-job' to create a job.
```

For the instance, the build\_image.sh script will build an image called 'sconecuratedimages/issre2019:radiomics-asperathos'. A proper 'config.json' is also generated, containing application MRENCLAVE, FSPF tag/key and image name, for further use by the job submission script. You can choose the tag for your convenience via script argument. Remember that this image must be accessible by Kubernetes cluster.

```bash
$ docker push sconecuratedimages/issre2019:radiomics-asperathos
The push refers to repository [sconecuratedimages/issre2019:radiomics-asperathos]
525fc223264a: Pushed 
401dbb9dd3d9: Pushed 
89b4d7ff538d: Pushed 
asperathos: digest: sha256:77e5f5334a7351335afffe87b81c5220484b04fac8c6436d044cda8c8cacb942 size: 954
```

### Step 4: Submit the job

```bash
$ usage: submit-job [-h] [--config CONFIG] [--cert CERT]
                  [--expected-time EXPECTED_TIME]
                  [--item-lease-secs ITEM_LEASE_SECS] [--verbosity VERBOSITY]
                  (--cas-address CAS_ADDRESS | --sgx-simulation)
                  --generate-json-only OUTPUT_JSON | --submissions-url
                  SUBMISSIONS_URL)
                  data-path

Submit data for batch processing using Asperathos

positional arguments:
  data-path             Set the data path

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Set the configuration file (default: config.json)
  --cert CERT           CAS API authentication certificate (default:
                        client.pem)
  --expected-time EXPECTED_TIME
                        Expected time (in secs) to finish the job (default:
                        200s)
  --item-lease-secs ITEM_LEASE_SECS
                        Expected time (in secs) to process an item (default:
                        15s)
  --verbosity VERBOSITY
                        Set verbosity level of SCONE (default: 0)
  --cas-address CAS_ADDRESS
                        Set the SCONE CAS address [host:REST port:attestation
                        port] (ex: 10.30.1.24:8081:18765)
  --sgx-simulation       Run using SGX simulation environment (default: False)
  --generate-json-only OUTPUT_JSON
                        Create an Asperathos job JSON file (do not submit)
  --submissions-url SUBMISSIONS_URL
                        Asperathos submissions API URL (ex:
                        http://10.11.16.34:1500/submissions)
```

Now, we are going to submit videos from path './sample-videos' and Asperathos submissions API listening on 'http://10.11.16.34:1500/submissions', with a deadline of 200s in SGX simulation mode:

Note: remember to change the Asperathos submissions API URL to a proper one.

```bash
$ ./submit-job ./sample-videos --sgx-simulation --generate-json-only my-job.json --expected-time 200
[INFO] Checking the CAS status...
[INFO] Generating AES128-GCM KEY...
[INFO] KEY = GWwNN/WfpPH0WeUnwUPLIQ==

[INFO] Creating container on Swift named '788bfbe2-3e82-4d5f-a140-165e8b24f192'

[INFO] Encrypting and publishing 'VH020213M4_001390_20160406T111556.MP4' (as '37b906c74d074b37a7a27bbd62534dae.mp4') on Swift

[INFO] Encrypting and publishing 'VH020213M4_001418_20160407T115035.MP4' (as '9eaa79df8eb24092a77f705b14bc9674.mp4') on Swift

[INFO] Encrypting and publishing 'VH020213M4_001559_20160429T120933.MP4' (as 'ebe27a99183944398dcd841abc29fb6c.mp4') on Swift

[INFO] Encrypting and publishing 'VH020213M4_001559_20160429T120845.MP4' (as '7be37296568d4880a49c1f8047787e62.mp4') on Swift

...

[INFO] Workload URL: https://cloud5.lsd.ufcg.edu.br:8080/swift/v1/788bfbe2-3e82-4d5f-a140-165e8b24f192/workload.txt


[INFO] 'my-job.json' generated successfully.
```

The 'my-job.json' contains the Asperathos job JSON which includes workload list URL, plugin configurations, visualizer credentials, etc. To submit the job, run:

```bash
$ curl -H "Content-Type: application/json" -X POST -d @my-job.json http://10.11.16.34:1500/submissions

{"job_id": "kj-3898be2"}
```

With the Job ID in hands, you could do a request to [submissions URL]/[job id] and check the progress of the job. For this instance:

```
$ curl http://10.11.16.34:1500/submissions/kj-3898be2

{"redis_port": 30150, "starting_time": "Job is not running yet!", "redis_ip": "10.11.16.84", "status": "created", "visualizer_url": "http://10.11.16.84:30735", "app_id": "kj-3898be2"}
```

You can see a live chart of the progress of your job accessing URL from the "visualizer_url" field, in this case we have "http://10.11.16.84:30735". The default credentias (username and password) to access the visualizer is:
```
username: admin
password: radiomics123
```

To use SGX hardware mode, just replace "--sgx-simulation" to "--cas-adress CAS-ADDRESS". For the instance:

```bash
$ ./submit-job ./sample-videos --cas-address scone.lsd.ufcg.edu.br:8081:18765 --submissions-url http://10.11.16.34:1500/submissions
```

This command will issue a job to Asperathos that listens on 10.11.16.34:1500 and will provide secrets to a Palaemon instance listening on 'scone.lsd.ufcg.edu.br'.
