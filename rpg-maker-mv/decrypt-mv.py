import binascii
import sys
import os
from os import path


def xor(data, key):
    l = len(key)
    return bytearray(((data[i] ^ key[i % l]) for i in range(0, len(data))))


class Decrypter:
    encrypt_table = {"rpgmvo": "ogg", "rpgmvm": "m4a", "rpgmvp": "png"}

    def __init__(self, gamedir):
        self.gamedir = gamedir

    def find_key(self):
        json = open(self.gamedir + "/data/System.json", "r").read()
        p1 = json.index("encryptionKey")
        p2 = json.index(':"', p1) + 2
        p3 = json.index('"}', p2)
        keystr = json[p2:p3]
        return bytearray(binascii.unhexlify(keystr))

    def list_encrypted_files(self, gamedir=None):
        files = []
        gamedir = gamedir or self.gamedir
        for i in os.listdir(gamedir):
            p = path.join(gamedir, i)

            if path.isdir(p):
                files += self.list_encrypted_files(p)
                continue

            ext = path.splitext(p)[1][1:]
            if ext in Decrypter.encrypt_table.keys():
                files.append(p)

        return files

    def decrypt_file(self, file, key):
        data = open(file, "rb").read()
        data = data[16:]  # remove rpg mv header
        cyphertext = data[:16]
        plaintext = xor(cyphertext, key)
        data = data[16:]  # remove encrypted header
        return plaintext + data

    def decrypt(self):
        key = self.find_key()
        files = self.list_encrypted_files()

        count = 1
        total = len(files)
        for file in files:
            filename = path.splitext(file)
            new_ext = Decrypter.encrypt_table[filename[1][1:]]
            data = self.decrypt_file(file, key)
            open(filename[0] + "." + new_ext, "wb").write(data)
            os.remove(file)

            print(f"{count}/{total} {file}")
            count += 1

        json_path = self.gamedir + "/data/System.json"
        data = open(json_path, "r").read()
        data = data.replace('"hasEncryptedImages":true', '"hasEncryptedImages":false')
        data = data.replace('"hasEncryptedAudio":true', '"hasEncryptedAudio":false')
        open(json_path, "w").write(data)
        open(self.gamedir + "/Game.rpgproject", "w").write("RPGMV 1.0.0")


def main():
    if len(sys.argv) != 2:
        print("usage: python decrypt-mv.py path_to_www")
        return

    Decrypter(sys.argv[1]).decrypt()


if __name__ == "__main__":
    main()
