#!/bin/sh
export PATH=$PASH:/usr/local/bin:/bin
cd /var/spool/cron
#定位含有任务的行并删除
sed -i '/cookie_fetch_periodically.sh/d' ${USER}
