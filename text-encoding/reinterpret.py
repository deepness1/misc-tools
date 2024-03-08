import sys
import codecs

if len(sys.argv) != 3:
    print("usage: reinterpret.py enc_from enc_to")
    print("convert stdin from enc_from to enc_to")
    exit(1)

enc_from = sys.argv[1]
enc_to = sys.argv[2]

for line in sys.stdin:
    dat = codecs.encode(line, encoding=enc_from, errors="ignore")
    res = codecs.decode(dat, encoding=enc_to, errors="ignore")
    print(res)
