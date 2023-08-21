#!/bin/bash
sudo setcap cap_net_bind_service=+ep $(pwd)/bin/caddy
