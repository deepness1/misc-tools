saveroot=$HOME/working/dl/repository
recordroot=$HOME/working/dl/repository-records

python src/dump.py illust users.csv $saveroot/comic $recordroot/comic
python src/dump.py novel novel.csv $saveroot/novel $recordroot/novel
