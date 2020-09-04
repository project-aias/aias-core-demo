import os
import random

import platform
import base64
import json

import ctypes
from ctypes import cdll, c_char_p, c_int32

from flask import Flask, request, json, jsonify, session

app = Flask(__name__)
app.secret_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxXo2zWkciUEZBcm/Exk8Zac8NWskP59EAVFlO218xIXOV0Ff
phPB/tnbQh7GDXddo7XVEptHdHXyJlXXLihb9vXbUZF2NDFLOhgDv7pa72VNLbw+
jKR/FlsDtwv/bv7ZDqq+n79uavuJ8giX3qCf+mtBmro7hG5AVve3JImhvA0FvTKJ
0xCYUYw02st08He5RwFAXQK8G2cwahp+5ECHMDdfFUaoxMfRN/+Hl9iqiJovKUJQ
3545N2fDYdd0eqSlqL1N5xJxYX1GDMtGZgMEhHR6ntdfm7r43HDB4hk/MJIsNay6
+K9tJBiz1qXG40G4NjMKzVrX9pi1Bv8G2RnP/wIDAQABAoIBAC3nRMnmvw1gpnJj
/Rhxa0qt3x8Dsr9fRC2SQBfaUYBVIivCNHukaBnXhlIOWTdUId4mLEtQ8QEvUYR7
u7MtCoOTjtGdIH7tXnE4l9Z/eRfg0lnpQhjrO+d0bJ6mGVAxyT7RjdIQa5hOtDgg
qzzC1a0eNXfEBoW4IxiUKGxD2eaeL2NEuwdysO8MrxvbpPLrK4KaQwansh5EdrvL
QmWtSSuB2rYVwWbp7Rs+NuKS4w7CRm9Zp6kN6yjBum+x2o3Wdj33Ww0HayeaRZ1i
nmVTyphfajKuDLYUavCo4tBE67LK/VHesxeFNM+6PjONUVmcRnT1eoATeLVE4vOO
M9kFUQECgYEA9WD+s2HpETsXxyWPp2wv1G8b2kZq0h85Vb971PwgRciHkBccHFHR
0Hgc/hFTHg86V0iVBbcsWtTNTsNbH7aXGNvWJVQiMPDNdKmavgAl3tpGRP7iffLF
503he0GQmVaDEBH4LqCi4Ix0u7wnOND9ie8hMzxtC+2cZyLY8y13o78CgYEAzgZu
JPMgD2BvSKDJYlP7j4OKj0+mQIdpW+ONuLZsbtTDs5GiggTeeeyQDvlESUMSypMj
rmS/GUHAnYft27YWjk48vlzrvrnLyzWLalGYLsUigQIf2BRJG43j8iXuuBKciOrf
P8dkByYXatkiA57CJXOJGJLPvMOfkr+p3i2L48ECgYA9eY52HIqKoZZkczmZRVZ6
T1fYCJpMiDwSCoYYpw3izcmAxPlq8uiw5NbGpEqBlmkUYv/KzchT/UpueC0FNfaG
6NSux3RFdJ7UooU9IsZaHa9LK9xMl50TRQS/n359nBn71bSq4d3MigPY4NumtV0/
yGQ19OaQ/XeYszdNPU/i+wKBgQCXSbeGIJaRVBJD9fYL43nd+A0+kZGW3xjqJh5C
3oqflFOlQDNiYKryQ1nB9R9E4SEiaowQGuENbfBAfbmX1o2XsDIA5AElTBAvx8D5
sLMc3RwqOeIibTsGJdqWTW6P8vLJxBduIT/90+XsS0gj+me80quAxQYRKmG6hE37
3dxUwQKBgQC2onc1n35vGlZ2HxWdnPOUyRnA8HNVXcskprR07ZqFQu36LxI8hHvz
O+zc6JPZDWBppJDWot9d5HeNEjDBMcSqcpeXXYU8XvxA+uECLPctLgNMWxyKFx95
0sVQIY0n9eLL7sg5aCUpGKf4Qc88wF8OPYnBzjCeiJusjkGhQ5rqdQ==
- ----ENDRSAPRIVATEKEY - ----"""

def verify_signature(data):
    lib = get_lib()

    with open("parameters/message.txt", 'rb') as f:
        message = f.read()
    with open("parameters/signer_pubkey.pem", 'rb') as f:
        signer_pubkey = f.read()
    with open("parameters/judge_pubkey.pem", 'rb') as f:
        judge_pubkey = f.read()

    lib.verify.restype = c_int32
    lib.verify.argtypes = (c_char_p, c_char_p, c_char_p)

    return lib.verify(data, signer_pubkey, judge_pubkey)

def verify_token(session, body):
    print("session:", session)
    try:
        data = json.loads(body)
        v = session['token'] == data['signed']['random']
        return v
    except Exception as e:
        print(f"error: {e}")
        return False

@app.route('/verify', methods=['POST'])
def index():
    valid_sig = verify_signature(request.get_data())
    valid_token = verify_token(session, request.get_data())
    valid = valid_sig and valid_token

    resp = {
        "result": bool(valid)
    }

    if valid:
        rng = random.SystemRandom()
        random_token = rng.randint(100000, 999999)

        resp['random'] = str(random_token)
        session['token'] = random_token

    return json.dumps(resp)


def get_lib():
    pf = platform.system()
    if pf == 'Darwin':
        return cdll.LoadLibrary("aias-auth-sdk/ffi/target/release/liblib.dylib")
    elif pf == 'Linux':
        return cdll.LoadLibrary("aias-auth-sdk/ffi/target/release/liblib.so")


if __name__ == "__main__":
    app.run()
