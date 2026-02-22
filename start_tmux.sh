#!/bin/bash
set -e

SESSION="glass_dashboard"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux attach -t "$SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n "streamlit"
tmux send-keys -t "$SESSION:0" "cd ~/proiecte/dashboard && source ~/proiecte/ml/bin/activate && streamlit run app.py" C-m

tmux split-window -h -t "$SESSION:0"
tmux send-keys -t "$SESSION:0.1" "cd ~/proiecte/dashboard && source ~/proiecte/ml/bin/activate && python3 agent_elite.py" C-m

tmux attach -t "$SESSION"
