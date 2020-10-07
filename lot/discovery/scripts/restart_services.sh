#!/bin/bash

proc_count=$(/bin/ps aux | /bin/grep 'celery worker' | /usr/bin/wc -l)
echo $proc_count

if [ $proc_count -lt 2 ]
  then
    cd /usr/local/apps/forestplanner/lot/
    /usr/local/apps/forestplanner/env/bin/celery worker --broker "redis://localhost:6379" -A lot
fi
