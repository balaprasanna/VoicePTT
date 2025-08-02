#!/bin/bash
cd /Users/bala/devlocal/macapps 
source whisper_env/bin/activate

# Run the app in background and detach from terminal
nohup python run_ptt.py > /dev/null 2>&1 &

# Optional: Show brief startup message then exit terminal
sleep 0.5
