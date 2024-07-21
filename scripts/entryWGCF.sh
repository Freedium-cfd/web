#!/usr/bin/env bash

set -e

_downwgcf() {
    echo
    echo "clean up"
    if ! wg-quick down wgcf; then
        echo "error down"
    fi
    echo "clean up done"
    exit 0
}

#-4|-6
runwgcf() {
    trap '_downwgcf' ERR TERM INT

    _enableV4="1"
    if [ "$1" = "-6" ]; then
        _enableV4=""
    fi

    if [ ! -e "wgcf-account.toml" ]; then
        wgcf register --accept-tos
    fi

    if [ -e "custom-wgcf-license.conf" ]; then
        _license_key=$(cat custom-wgcf-license.conf)
        _old_license_key=$(awk -F "['']" '/license_key/{print $2}' wgcf-account.toml)
        if [ "$_license_key" != "$_old_license_key" ]; then
            echo 'updating license key'
            sed -i "s/license_key.*$/license_key = '${_license_key}'/" wgcf-account.toml
            wgcf update
        fi
    fi

    if [ ! -e "wgcf-profile.conf" ]; then
        wgcf generate
    else
        _account_file_private_key=$(awk -F "['']" '/private_key/{print $2}' wgcf-account.toml)
        _profile_file_private_key=$(awk -F " = " '/PrivateKey/{print $2}' wgcf-profile.conf)
        if [ "$_account_file_private_key" != "$_profile_file_private_key" ]; then
            echo 're generate profile'
            wgcf generate
        fi
    fi

    if [ -e "custom-wgcf-endpoint.conf" ]; then
        _endpoint=$(cat custom-wgcf-endpoint.conf)
        sed -i "s/Endpoint.*$/Endpoint = ${_endpoint}/" wgcf-profile.conf
    fi

    cp wgcf-profile.conf /etc/wireguard/wgcf.conf

    DEFAULT_GATEWAY_NETWORK_CARD_NAME=$(route | grep default | awk '{print $8}' | head -1)
    DEFAULT_ROUTE_IP=$(ifconfig $DEFAULT_GATEWAY_NETWORK_CARD_NAME | grep "inet " | awk '{print $2}' | sed "s/addr://")

    echo ${DEFAULT_GATEWAY_NETWORK_CARD_NAME}
    echo ${DEFAULT_ROUTE_IP}

    sed -i "/\[Interface\]/a PostDown = ip rule delete from $DEFAULT_ROUTE_IP  lookup main" /etc/wireguard/wgcf.conf
    sed -i "/\[Interface\]/a PostUp = ip rule add from $DEFAULT_ROUTE_IP lookup main" /etc/wireguard/wgcf.conf

    if [ "$1" = "-6" ]; then
        sed -i 's/AllowedIPs = 0.0.0.0/#AllowedIPs = 0.0.0.0/' /etc/wireguard/wgcf.conf
    elif [ "$1" = "-4" ]; then
        sed -i 's/AllowedIPs = ::/#AllowedIPs = ::/' /etc/wireguard/wgcf.conf
    fi

    modprobe ip6table_raw

    wg-quick up wgcf

    if [ "$_enableV4" ]; then
        _checkV4
    else
        _checkV6
    fi

    echo
    echo
    echo "wgcf status"
    wgcf status

    echo
    echo "OK, wgcf is up."

    sleep infinity &
    wait

}

_checkV4() {
    echo "Checking network status, please wait...."
    while ! curl --max-time 2 ipinfo.io; do
        wg-quick down wgcf
        echo "Sleep 2 and retry again."
        sleep 2
        wg-quick up wgcf
    done

}

_checkV6() {
    echo "Checking network status, please wait...."
    while ! curl --max-time 2 -6 ipv6.google.com; do
        wg-quick down wgcf
        echo "Sleep 2 and retry again."
        sleep 2
        wg-quick up wgcf
    done

}

if [ -z "$@" ] || [[ "$1" = -* ]]; then
    runwgcf "$@"
else
    exec "$@"
fi
