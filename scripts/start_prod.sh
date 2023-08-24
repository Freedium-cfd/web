#!/bin/bash

if [ -z "$TELEGRAM_ADMIN_ID" ]; then echo "TELEGRAM_ADMIN_ID var is blank"; else echo "TELEGRAM_ADMIN_ID var is set to '$TELEGRAM_ADMIN_ID'"; fi
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then echo "TELEGRAM_BOT_TOKEN var is blank"; else echo "TELEGRAM_BOT_TOKEN var is set to '$TELEGRAM_BOT_TOKEN'"; fi

arch=$(dpkg --print-architecture)
echo $arch

redis-cli flushall
./bin/$arch/caddy run --config CaddyfileProd &
CADDY_PID=$!
python3 -m server server &
SERVER_PID=$!

function onexit() {
        echo "onexit"
        sleep 25
        kill $CADDY_PID
        kill $SERVER_PID
}
trap onexit EXIT

sendMessageTelegram(){
    echo ${1}
    local message=${1}

    curl -X POST \
         -H 'Content-Type: application/json' \
         -d "{\"chat_id\":\"$TELEGRAM_ADMIN_ID\",\"text\":\"$message\"}" \
         "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage"
}

while true
do
  CHECK_CADDY_PID=$(ps -A| grep $CADDY_PID |wc -l)
  if [[ $CHECK_CADDY_PID -eq 0 ]]; then
          sendMessageTelegram "Restarting caddy, since it's down"
          ./bin/$arch/caddy start --config CaddyfileProd &
          CADDY_PID=$!
  fi

  CHECK_SERVER_PID=$(ps -A| grep $SERVER_PID |wc -l)
  if [[ $CHECK_SERVER_PID -eq 0 ]]; then
        sendMessageTelegram "Restarting server, since it's down"
        python3 -m server server &
        SERVER_PID=%!
  fi

  sleep 5

  backend_service_url="http://localhost:7080"
  backend_status_code=$(curl -m 10 -s -o /dev/null -w "%{http_code}" "$backend_service_url")

  if [ "$backend_status_code" -lt 200 ]; then
    sendMessageTelegram "Restarting backend, since it's down"
    kill $SERVER_PID
    python3 -m server server &
    SERVER_PID=$!
  fi

  reverse_service_url="http://localhost"
  reverse_status_code=$(curl -m 10 -s -o /dev/null -w "%{http_code}" "$reverse_service_url")

  if [ "$reverse_status_code" -lt 308 ]; then
    sendMessageTelegram "Restarting reverse, since it's down"
    kill $CADDY_PID
    ./bin/$arch/caddy start --config CaddyfileProd &
    CADDY_PID=$!
  fi

  sleep 65
done

