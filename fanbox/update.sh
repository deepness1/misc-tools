saveroot=$HOME/working/dl/repository
recordroot=$HOME/working/dl/repository-records

python src/dump.py users.csv $saveroot/comic $recordroot/comic
python src/dump.py novelists.csv $saveroot/novel $recordroot/novel
