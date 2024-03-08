import os
import sys
import shutil

if len(sys.argv) != 4:
    print("usage: python3 replace-rtp.py path_to_rtp path_to_target path_to_backup")
    exit(0)

rtp = os.path.abspath(sys.argv[1])
target = os.path.abspath(sys.argv[2])

for root, subdirs, files in os.walk(target):
    for file in files:
        target_path = os.path.join(root, file)
        target_rel = os.path.relpath(target_path, target)
        rtp_path = os.path.join(rtp, target_rel)

        if not os.path.isfile(rtp_path) or os.path.islink(target_path):
            continue

        if False:  # check size
            target_size = os.path.getsize(target_path)
            rtp_size = os.path.getsize(rtp_path)
            if target_size != rtp_size:
                print("file size not match:", target_size)
                continue

        backup_path = os.path.join(sys.argv[3], target_rel)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.move(target_path, backup_path)
        os.symlink(os.path.relpath(rtp_path, os.path.dirname(target_path)), target_path)
        print(target_rel)

game_ini_path = os.path.join(target, "Game.ini")
if not os.path.isfile(game_ini_path):
    print("Game.ini not found. skipping...")
else:
    file = open(game_ini_path, "rb").read()
    file.replace("RTP=RPGVXAce".encode(), "RTP=".encode())
    file += "FullPackageFlag=true".encode()
    open(game_ini_path, "wb").write(file)
