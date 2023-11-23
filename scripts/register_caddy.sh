#!/bin/bash
sudo setcap cap_net_bind_service=+ep $(pwd)/bin/x86_64/caddy
