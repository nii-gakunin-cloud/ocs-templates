#!/bin/bash

# このスクリプトがシグナルで終了するとき、途中でデーモンになる rpcbind, rpc.statsdを終了させる
# どちらも個別のpgidを持ってしまい、process groupでkillするのも難しい
trap 'echo signal; killall rpcbind; killall rpc.statd' SIGINT SIGTERM SIGKILL SIGQUIT

set -o errexit
set -o pipefail

echo "/export *(rw,sync,no_subtree_check,fsid=0,no_root_squash)" > /etc/exports

exportfs -a
rpcbind
rpc.statd
rpc.nfsd

# -F でフォアグラウンド実行
rpc.mountd -F
