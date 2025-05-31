import os
import sys
import json

magic = bytes(
    [
        0x52, # R
        0x50, # P
        0x47, # G
        0x4D, # M
        0x56, # V
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)

def decrypt(root):
    for cwd, dirs, files in os.walk(root):
        for file in files:
            if file[-1] != "_":
                continue
            path = cwd + "/" + file
            print(path)
            enc = open(path, "rb").read()
            if enc[:len(magic)] != magic:
                continue
            body = bytearray(enc[len(magic):])
            for i in range(len(enc_key)):
                body[i] ^= enc_key[i]
            open(path[:-1], "wb").write(body)
            os.remove(path)

basedir = sys.argv[1]
system = json.load(open(f"{basedir}/data/System.json"))
image_enc = system["hasEncryptedImages"]
audio_enc = system["hasEncryptedAudio"]
enc_key = bytes.fromhex(system["encryptionKey"])

#if image_enc:
#    decrypt(f"{basedir}/img")
#
#if audio_enc:
#    decrypt(f"{basedir}/audio")

system["hasEncryptedImages"] = False
system["hasEncryptedAudio"] = False
json.dump(system, open(f"{basedir}/data/System.json", "w"))

print("done")
