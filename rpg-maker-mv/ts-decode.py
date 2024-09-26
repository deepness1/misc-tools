# decode xor-ed scenario file
# example: % mkdir scenario-d
#          % for file in scenario/*; do python /tmp/decode.py $file > scenario-d/${file:t}; done
#          rename *.sl to *.txt
#          then replace "Decode":"true" to "false" at ts_decode in plugins.js

import os
import sys

key = 255
for c in open(sys.argv[1], "r").read():
    print(chr(ord(c) ^ key), end="")
