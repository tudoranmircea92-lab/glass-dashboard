#!/bin/bash

SESSION=dashboard

tmux new-session -d -s $SESSION

# pane 1 - Streamlit
tmux send-keys -t $SESSION "cd ~/proiecte/dashboard && source ~/proiecte/ml/bin/activate && streamlit run app.py" C-m

# pane 2 - Agent
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION "cd ~/proiecte/dashboard && source ~/proiecte/ml/bin/activate && python3 agent_elite.py" C-m

tmux attach -t $SESSION
