#!/bin/bash

. $(dirname $0)/slurm-functions.sh
. $(dirname $0)/../vcpsdk/config/env

CLEANUP_NODE_WAIT_TIME="${CLEANUP_NODE_WAIT_TIME:-600}"  # default 10min
VCP_SDK_CONTAINER_IMAGE="${VCP_SDK_CONTAINER_IMAGE:-vcpsdk:20.10.0}"
NFS_LOCAL_DIR="${NFS_LOCAL_DIR:-/mnt}"

#
# ジョブ実行先ノードを 1 ノード追加する
#
# - VCP SDK を使用し、環境変数 VC_NAME に指定した Unit Group に対して
# - VC Node 1 個を含む Unit を作成 (create_unit) する。
# - Unit の spec は環境変数 PROVIDER_NAME, FLAVOR_NAME, IMAGE_NAME から取得する。
# - 起動したノードは、クラスタの共有ファイルシステム (NFS) をマウントする。
# 
add_node () {
    echo "Creating VC Node ..."

    tmpkey=$(mktemp "/tmp/${0##*/}.tmpXXXXXX")
    rm "${tmpkey}" && ssh-keygen -t ed25519 -f "${tmpkey}" -N "" >/dev/null

    cd $(dirname $0)/../vcpsdk/
    nodeip=$(sudo docker run --rm \
                 -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
                 -v "${tmpkey}".pub:/tmp/key.pub \
                 -e VCP_ACCESSKEY="${VCP_ACCESSKEY}" \
                 -e VC_NAME="${VC_NAME}" \
                 -e IMAGE_NAME="${IMAGE_NAME}" \
                 -e PROVIDER_NAME="${PROVIDER_NAME}" \
                 -e FLAVOR_NAME="${FLAVOR_NAME}" \
                 "${VCP_SDK_CONTAINER_IMAGE}" add_vcnode.py)

    exit_status=$?
    if [ -z "${nodeip}" ] || [ $exit_status -ne 0 ]; then
        echo "Error!! add VC node failed."
        return
    fi

    echo "Created VC Node: $nodeip"

    # 起動したノード上で NFS マウントを実行する
    ssh -i "${tmpkey}" -o StrictHostKeyChecking=no root@"${nodeip}" \
        sh -c "rpcbind && mount -t nfs ${NFS_MOUNT_POINT} ${NFS_LOCAL_DIR}"

    # 起動したノードの hostname を取得し、クラスタへの組み込み処理をする
    echo "Joining Cluster ..."
    nodename=$(ssh -i "${tmpkey}" root@"${nodeip}" uname -n)
    join_cluster ${nodename}

    rm ${tmpkey} ${tmpkey}.pub
}

#
# ジョブ実行先ノードを *すべて* 削除する
#
# VCP SDK を使用し、環境変数 VC_NAME に指定した Unit Group に含まれるすべての
# VC Node を一括削除する。
#
cleanup () {
    # 稼働中ノードの一覧を取得
    cd $(dirname $0)/../vcpsdk/
    vcnodes=$(sudo docker run --rm \
        -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
        -e VCP_ACCESSKEY="${VCP_ACCESSKEY}" \
        -e VC_NAME="${VC_NAME}" \
        "${VCP_SDK_CONTAINER_IMAGE}" get_vcnode.py)

    if [ -z "${vcnodes}" ];then
        return  # no running node, nothing to do
    fi

    # 削除対象ノードのクラスタからの切り離し
    for nodename in ${vcnodes}; do
        leave_cluster ${nodename}
    done

    # すべてのノードが属する UnitGroup を削除
    echo "Deleting all VC Node ..."
    cd $(dirname $0)/../vcpsdk/
    sudo docker run --rm \
        -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
        -e VCP_ACCESSKEY="${VCP_ACCESSKEY}" \
        -e VC_NAME="${VC_NAME}" \
        -e IMAGE_NAME="${IMAGE_NAME}" \
        -e PROVIDER_NAME="${PROVIDER_NAME}" \
        -e FLAVOR_NAME="${FLAVOR_NAME}" \
        "${VCP_SDK_CONTAINER_IMAGE}" cleanup_vc.py
}

#
# Hybrid Cloud Service のメイン制御
#
# 1. キューのノード実行状況を確認し、実行待ちジョブがあればノードを追加する。
# 2. 実行待ちジョブが無い場合、CLEANUP_NODE_WAIT_TIME 秒間だけ待つ。
# 3. 再度ノード実行状況を確認し、実行待ち、実行中ジョブがどちらも無い場合、
#    全ノードを削除する。
# 4. 再度、1 の処理から繰り返す。
#
do_start () {
    while : ; do
        get_status

        echo "$RUN_COUNT jobs running / $WAIT_COUNT jobs waiting"

        if [ $WAIT_COUNT -gt 0 ]; then
            add_node
        else
            sleep $CLEANUP_NODE_WAIT_TIME
            get_status

            if [ $WAIT_COUNT -eq 0 ] && [ $RUN_COUNT -eq 0 ]; then
                cleanup
            fi
        fi

        sleep 4
    done
}

check_version || ("Some required software is not installed."; exit 1)

do_start

exit 0
