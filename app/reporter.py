#!/usr/bin/env python

import sys

def report_error(subprocess, item):
    """
        report_error checks the errors in the execution of an item, deciding
        what to do with the current item.
        - param: subprocess the item execution
    """
    # Check if attestation process was completed
    o, err = subprocess.communicate()
    print(err)
    if "Error receiving config response from CAS!" in err:
        return (False, (item, "ERROR: The attestation process was not completed, check application data"))

    if "Connecting to CAS failed!" in err:
        return (False, (item, "ERROR: Unable to attest application, contact administration"))
    
    if "ATTESTATION: Didn't receive quote response from quoting service" in err:
        return (False, (item, "ERROR: The attestation process was not completed, check application"))

    return (True, (o, err))

