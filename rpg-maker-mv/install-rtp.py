import os
import sys
import shutil

if len(sys.argv) != 3:
    print("usage: python3 install-rtp.py path_to_rtp path_to_target")
    exit(0)

rtp = os.path.abspath(sys.argv[1])
target = os.path.abspath(sys.argv[2])

for root, subdirs, files in os.walk(rtp):
    for file in files:
        rtp_path = os.path.join(root, file)
        rtp_rel = os.path.relpath(rtp_path, rtp)
        target_path = os.path.join(target, rtp_rel)

        if os.path.isfile(target_path):
            continue

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        os.symlink(os.path.relpath(rtp_path, os.path.dirname(target_path)), target_path)
        print(rtp_rel)

game_ini_path = os.path.join(target, "Game.ini")
if not os.path.isfile(game_ini_path):
    print("Game.ini not found. skipping...")
else:
    file = open(game_ini_path, "rb").read()
    file.replace(b"RTP=RPGVXAce", b"RTP=")
    file += b"FullPackageFlag=true"
    open(game_ini_path, "wb").write(file)
