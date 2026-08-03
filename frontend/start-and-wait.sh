#!/bin/sh
set -eu

shutdown_file="${SHUTDOWN_FILE:-/run-status/pipeline-finished}"
mkdir -p "$(dirname "$shutdown_file")"
chmod 0777 "$(dirname "$shutdown_file")"
rm -f "$shutdown_file"

node server.js &
server_pid=$!

stop_server() {
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}

trap 'stop_server; exit 0' INT TERM

while kill -0 "$server_pid" 2>/dev/null; do
  if [ -f "$shutdown_file" ]; then
    echo "Pipeline finalizado; encerrando o front-end."
    stop_server
    exit 0
  fi
  sleep 1
done

wait "$server_pid"
