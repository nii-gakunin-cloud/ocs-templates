#
# SLURM functions
#

#
# 監視対象の SLURM PARTITION 名
#
PARTITION="${QUEUE_NAME:-cloud}"

#
# squeue - view information about jobs located in the Slurm scheduling queue.
# https://slurm.schedmd.com/squeue.html
#
JOB_STATUS_COMMAND="squeue"

#
# JOB STATE CODES
# PD=PENDING, R=RUNNING
#
WAIT_STAT="PD"
RUN_STAT="R"

#
# キューのノード実行状況を取得し、実行待ちまはた実行中ジョブの個数を集計する
#
# e.g. squeue コマンド実行時出力:
#   JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
#      18     cloud   run.sh   ubuntu PD       0:00      1 (Resources)
#      21     xxxxx   run.sh   ubuntu  R       0:00      1 (Priority)
#      19     cloud   run.sh   ubuntu PD       0:00      1 (Priority)
#      20     cloud   run.sh   ubuntu PD       0:00      1 (Priority)
#      17     cloud   run.sh   ubuntu  R       0:50      1 c1
#
# e.g. squeue コマンド出力結果の集計:
#   3 PD
#   1 R
# 
get_status () {
    WAIT_COUNT=0
    RUN_COUNT=0

    while read line; do
        stats=($line)
        if [ "${stats[1]}" = "${WAIT_STAT}" ]; then
            WAIT_COUNT="${stats[0]}"
        elif [ "${stats[1]}" = "${RUN_STAT}" ]; then
            RUN_COUNT="${stats[0]}"
        fi 
    done < <("${JOB_STATUS_COMMAND}" | \
             awk -v queue="${PARTITION}" '{if($2==queue) print $5}' | sort | uniq -c)
}

#
# 起動したノードでジョブを実行可能な状態にする
#
join_cluster () {
    if [ -n $1 ]; then
        sudo scontrol update node=$1 state=idle
    fi
}

#
# シャットダウンするノードをクラスタから切り離すために "DRAIN" 状態に更新する
#
# cf. https://slurm.schedmd.com/scontrol.html
# > If you want to remove a node from service, you typically want to set its state to "DRAIN".
#
leave_cluster () {
    if [ -n $1 ]; then
        sudo scontrol update node=$1 state=drain reason=downing
    fi
}

#
# 使用するジョブ管理コマンドが実行可能かどうかを確認する
#
check_version () {
    "${JOB_STATUS_COMMAND}" --version
}
