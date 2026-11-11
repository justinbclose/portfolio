"""Decrypt stats.enc.json -> stats.json for the private dashboard. Usage: DASH_KEY=... python3 decrypt.py IN OUT"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
f = json.load(open(sys.argv[1])); b = base64.b64decode
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b(f["salt"]), iterations=f["iter"]).derive(os.environ["DASH_KEY"].encode())
data = json.loads(AESGCM(key).decrypt(b(f["iv"]), b(f["data"]), None))
json.dump(data, open(sys.argv[2], "w"), separators=(",", ":"))
print("ok", data["generated_at"], "sample" if data.get("sample") else "real")
