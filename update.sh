#!/bin/zsh

dir="${0:a:h}"
tmux neww -a -d "source env && cd '$dir/fanbox'  && ./update.sh || read"
tmux neww -a -d "source env && cd '$dir/fantia'  && ./update.sh || read"
tmux neww -a -d "source env && cd '$dir/kemono'  && ./update.sh || read"
tmux neww -a -d "source env && cd '$dir/pixiv'   && ./update.sh || read"
tmux neww -a -d "source env && cd '$dir/twitter' && ./update.sh || read"
