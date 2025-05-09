#!/bin/sh
# Start the first process (ui) in the foreground
cd vendor-invoice-processor-chat/ && npm run dev &
# Wait for 5 seconds
sleep 5

# Start the second process (uv) in the foreground
uv run main.py --host 0.0.0.0 --port 8000
