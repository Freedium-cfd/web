#!/bin/bash

arch=$(lscpu | grep Architecture | awk {'print $2'})
echo $arch

redis-cli flushall
./bin/$arch/caddy run --config ./CaddyfileMaintance