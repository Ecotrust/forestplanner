#!/bin/bash

sleep 5

/usr/sbin/service nginx restart

TIME=`/bin/date +20%y/%m/%d-%H:%M:%S`

/bin/echo $TIME' - nginx restarted' >> /var/log/rc.local.log 2>&1
