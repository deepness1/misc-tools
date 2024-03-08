#!/bin/zsh

dir="${0:a:h}"
tmux neww -d "source env && cd '$dir/fanbox' && ./update.sh"
tmux neww -d "source env && cd '$dir/fantia' && ./update.sh"
tmux neww -d "source env && cd '$dir/kemono' && ./update.sh"
tmux neww -d "source env && cd '$dir/pixiv' && ./update.sh"
