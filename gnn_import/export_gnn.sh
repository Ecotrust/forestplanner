#!/bin/bash
for TT in $(mdb-tables gnn_sppsz_db.mdb); do
    echo $TT
    mdb-export -Q -d '\t' -D '%Y-%m-%d %H:%M:%S' gnn_sppsz_db.mdb "$TT" > "${TT}.tsv"
done
