#!/bin/bash

if [ "$#" == "1" ]; then
  if [ "$1" -gt "0" ]; then
    iteration_count=$(expr $1 - 1)
  else
    iteration_count="$1"
  fi
else
  iteration_count=0
  echo "No start value given. Assuming 0"
fi
complete=0
# echo "$iteration_count"
while [[ "$complete" -le "0" ]]; do
    echo "-------------------------------"
    echo "-------------------------------"
    echo "--ITERATION: $iteration_count--"
    echo "-------------------------------"
    echo "-------------------------------"
    # iteration_count=`/usr/local/venv/lot/bin/python /usr/local/apps/land_owner_tools/lot/test_100.py "$iteration_count"`
    iteration_count=`/usr/local/venv/lot/bin/python /usr/local/apps/land_owner_tools/lot/load_new_conditions.py "$iteration_count"`
    result=$?
    echo "$iteration_count"
    iteration_count=`echo "$iteration_count" | sed -e '$!d'`
    if [ "$result" == "1" ]; then
        echo "$iteration_count"
        complete=1;
    fi
    if [ "$iteration_count" == "done" ]; then
        complete=1;
    fi
done
echo "Done."
