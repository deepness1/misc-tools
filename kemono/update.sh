saveroot=$HOME/working/dl/repository
recordroot=$HOME/working/dl/repository-records

python src/dump.py users.csv $saveroot/comic $recordroot/comic &&
python src/dump.py video.csv $saveroot/movie $recordroot/movie &&
python src/dump.py novel.csv $saveroot/novel $recordroot/novel
