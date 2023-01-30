#!/bin/bash
# 30 3 * * * /srv/optool/backup_log_s3.sh  > /dev/null 2>&1 &

FILE_LIST=("catalina" "access" "gzclean" "metric")
KEEP_DAYS=15
QSCTL_BIN="/srv/python2/bin/qsctl"
LOG_FILE="/data/log/rsync/backup.log"
zone="zjk"
BUCKET="logbackup"
BUCEKT_AK="USBGGKCNSRBXCAZUWVZT"
BUCEKT_SK="El3OJBg8JTCUxjxCxFa9HS9V5lKfGZFs1VG1TsNK"

[ ! -d `dirname $LOG_FILE` ] && mkdir -p `dirname $LOG_FILE`

function log(){
    level=$1
    message=$2
    echo "`date "+%F %H:%M"` [${level}] $message" >> ${LOG_FILE}.`date +%F`
}

function install_qsctl(){
    if [ ! -f $QSCTL_BIN ]; then
        /srv/python2/bin/pip install qsctl &>/dev/null
        if [ $? -ne 0 ]; then
            message="install qsctl error"
            log "ERROR" "${message}"
        else
            message="install qsctl succuss"
            log "INFO" "${message}"
            mkdir -p /root/.qingstor
cat >/root/.qingstor/config.yaml <<EOF
host: 'qingstor.com'
port: 443
protocol: 'https'
connection_retries: 3
# Valid levels are 'debug', 'info', 'warn', 'error', and 'fatal'.
log_level: 'info'
access_key_id: '${BUCEKT_AK}'
secret_access_key: '${BUCEKT_SK}'
EOF
            message="config qsctl succuss"
            log "INFO" "${message}"
        fi
    fi
}

function backup(){
    zone_name=$1
    ${QSCTL_BIN} sync /data/warehouse/logs/ qs://$BUCKET/${zone_name}/log/  --rate-limit 204800K
    if [ $? -ne 0 ]; then
        message="backup log fail"
        log "ERROR" "${message}"
    else
        message="backup log succuss"
        log "INFO" "${message}"
        for name in ${FILE_LIST[*]}
        do
            find /data/warehouse/logs/ -type f -mtime +${KEEP_DAYS} -name "${name}*"|xargs rm -f
        done
    fi
    ${QSCTL_BIN} sync /data/warehouse/bigdata/ qs://$BUCKET/${zone_name}/bigdata/  --rate-limit 204800K
    if [ $? -ne 0 ]; then
        message="backup bigdata fail"
        log "ERROR" "${message}"
    else
        message="backup bigdata succuss"
        log "INFO" "${message}"
        find /data/warehouse/bigdata/ -type f -mtime +${KEEP_DAYS}|xargs rm -f
    fi
}

function main(){
    install_qsctl
    backup $zone
}
main
