#
# Torque functions
#

#
# 監視対象の Torque QUEUE 名
#
QUEUE="${QUEUE_NAME:-cloud}"

#
# qstat - Show status of PBS batch jobs.
# http://docs.adaptivecomputing.com/torque/6-1-2/adminGuide/torque.htm#topics/torque/commands/qstat.htm
#
JOB_STATUS_COMMAND="qstat"

#
# job state:
#   Q=Job is queued, eligible to run or routed.
#   R=Job is running.
#
WAIT_STAT="Q"
RUN_STAT="R"

WAIT_COUNT=0
RUN_COUNT=0

#
# キューのノード実行状況を取得し、実行待ちまはた実行中ジョブの個数を集計する
#
# e.g. qstat コマンド実行時出力:
#   Job id                    Name             User            Time Use S Queue
#   ------------------------- ---------------- --------------- -------- - -----
#   2.master                  STDIN            ubuntu                 0 R cloud
#   3.master                  STDIN            ubuntu                 0 Q cloud
#   4.master                  STDIN            ubuntu                 0 Q xxxx
#   5.master                  STDIN            ubuntu                 0 Q cloud
#   6.master                  STDIN            ubuntu                 0 R xxxx
#
# e.g. qstat コマンド出力結果の集計:
#   2 Q
#   1 R
#
get_status () {
    while read line; do
        stats=($line)
        if [ "${stats[1]}" = "${WAIT_STAT}" ]; then
            WAIT_COUNT="${stats[0]}"
        elif [ "${stats[1]}" = "${RUN_STAT}" ]; then
            RUN_COUNT="${stats[0]}"
        fi 
    done < <("${JOB_STATUS_COMMAND}" | \
             awk -v queue="${QUEUE}" '{if($6==queue) print $5}' | sort | uniq -c)
}

#
# 起動したノードでジョブを実行可能な状態にするために必要な処理
#
join_cluster () {
    # not implemented
    : ;
}

#
# シャットダウンするノードをクラスタから切り離すために必要な処理
#
leave_cluster () {
    # not implemented
    : ;
}

#
# 使用するジョブ管理コマンドが実行可能かどうかを確認する
#
check_version () {
    "${JOB_STATUS_COMMAND}" --version
}
