#!/bin/bash
arch=$(lscpu | grep Architecture | awk {'print $2'})

sudo setcap cap_net_bind_service=+ep $(pwd)/bin/${arch}/caddy
