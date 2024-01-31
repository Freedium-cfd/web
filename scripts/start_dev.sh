#!/bin/bash

# Same script as start_prod, but adopted to dev environment

check_env_var() {
    if [[ -z "${!1}" ]]; then
        echo "$1 var is blank"
    else
        echo "$1 var is set to '${!1}'"
    fi
}

check_env_var "TELEGRAM_ADMIN_ID"
check_env_var "TELEGRAM_BOT_TOKEN"

arch=$(lscpu | grep Architecture | awk {'print $2'})
echo $arch

redis-cli flushall
./bin/$arch/caddy run --config CaddyfileDev &
CADDY_PID=$!
PYTHONASYNCIODEBUG=1 python3 -m server server &
SERVER_PID=$!

onexit() {
        echo "onexit"
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
  sleep 15

  CHECK_CADDY_PID=$(ps -A| grep $CADDY_PID |wc -l)
  if [[ $CHECK_CADDY_PID -eq 0 ]]; then
          # sendMessageTelegram "Restarting caddy, since it's down"
          ./bin/$arch/caddy start --config CaddyfileDev &
          CADDY_PID=$!
  fi

  CHECK_SERVER_PID=$(ps -A| grep $SERVER_PID |wc -l)
  if [[ $CHECK_SERVER_PID -eq 0 ]]; then
        # sendMessageTelegram "Restarting server, since it's down"
        PYTHONASYNCIODEBUG=1 python3 -m server server &
        SERVER_PID=%!
  fi

  sleep 35

  backend_service_url="http://localhost:7080"
  backend_status_code=$(curl -m 10 -s -o /dev/null -w "%{http_code}" "$backend_service_url")

  if [ "$backend_status_code" -lt 200 ]; then
    sendMessageTelegram "Restarting backend, since it's down"
    kill $SERVER_PID
    PYTHONASYNCIODEBUG=1 python3 -m server server &
    SERVER_PID=$!
  fi

  reverse_service_url="http://localhost:6752"
  reverse_status_code=$(curl -m 10 -s -o /dev/null -w "%{http_code}" "$reverse_service_url")

  if [ "$reverse_status_code" -lt 200 ]; then
    sendMessageTelegram "Restarting reverse, since it's down"
    kill $CADDY_PID
    ./bin/$arch/caddy start --config CaddyfileDev &
    CADDY_PID=$!
  fi

  sleep 65
done

