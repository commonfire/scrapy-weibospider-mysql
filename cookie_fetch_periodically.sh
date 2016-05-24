#!/bin/sh
export PATH=$PATH:/usr/local/bin
#判断是否存在crontab任务
if grep -Fxq "0 0 */1 * * bash /home/hadoop_user/scrapy-weibospider-mysql/cookie_fetch_periodically.sh >> /tmp/out.log 2>&1" /var/spool/cron/${USER}
then
    cd /home/hadoop_user/scrapy-weibospider-mysql/
    nohup scrapy crawl cookie_fetch_periodically >> cookie.log 2>&1 &
else
    cronfile='/tmp/crontab.${USER}'
    echo "0 0 */1 * * bash /home/hadoop_user/scrapy-weibospider-mysql/cookie_fetch_periodically.sh >> /tmp/out.log 2>&1" >> $cronfile
    crontab $cronfile  #执行crontab任务
    rm -rf $cronfile
    cd /home/hadoop_user/scrapy-weibospider-mysql/
    nohup scrapy crawl cookie_fetch_periodically >> cookie.log 2>&1 &
fi
