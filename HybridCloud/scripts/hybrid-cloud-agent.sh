#!/bin/bash

. $(dirname $0)/slurm-functions.sh

CLEANUP_NODE_WAIT_TIME="${CLEANUP_NODE_WAIT_TIME:-600}"  # default 10min
VCP_SDK_CONTAINER_IMAGE="${VCP_SDK_CONTAINER_IMAGE:-harbor.vcloud.nii.ac.jp/vcpsdk/vcpsdk:22.10.0}"

cd $(dirname $0)/../vcpsdk

add_node () {
    echo "Creating VC Node ..."

    nodename=$(sudo docker run --rm --net=host \
                   -v $(pwd)/config:/vcp_config \
                   --env-file=config/env \
                   "${VCP_SDK_CONTAINER_IMAGE}" ./add_vcnode.py \
               | tee out.txt \
               | grep AddNodeName | cut -f2)

    exit_status=$?
    if [ -z "${nodename}" ] || [ $exit_status -ne 0 ]; then
        echo "Error!! add VC node failed."
        return
    fi

    echo "Created VC Node: $nodename"
    join_cluster ${nodename}
}

delete_node () {
    echo "Deleting VC Node ..."

    nodename=$(sudo docker run --rm --net=host \
                   -v $(pwd)/config:/vcp_config \
                   --env-file=config/env \
                   "${VCP_SDK_CONTAINER_IMAGE}" ./delete_vcnode.py \
               | tee out.txt \
               | grep DeleteNodeName | cut -f2)

    exit_status=$?
    if [ -z "${nodename}" ] || [ $exit_status -ne 0 ]; then
        echo "No deletable nodes found, or an error occurred during deletion."
        return
    fi

    echo "Deleted VC Node: $nodename"
    leave_cluster ${nodename}
}

#
# Hybrid Cloud Service のメイン制御
#
# 1. キューのノード実行状況を確認し、実行待ちジョブがあれば1ノードを追加する。
# 2. 実行待ちジョブが無い場合、CLEANUP_NODE_WAIT_TIME 秒間だけ待つ。
# 3. 再度ノード実行状況を確認し、実行待ち、実行中ジョブがどちらも無い場合、
#    1ノードを削除する。
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
                delete_node
            fi
        fi

        sleep 4
    done
}

check_version || ("Some required software is not installed."; exit 1)

do_start

exit 0
