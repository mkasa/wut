
script_dir=$(dirname $0:A)
if [ -d "$script_dir/.venv" ]; then
    source $script_dir/.venv/bin/activate
fi
alias wip="git commit -am 'WIP'"
