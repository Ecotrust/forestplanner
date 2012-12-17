#!/bin/bash
#for TT in $(mdb-tables IDB_Version_2.mdb); do
#    echo $TT
#    mdb-export -Q -d '\t' -D '%Y-%m-%d %H:%M:%S' IDB_Version_2.mdb "$TT" > "${TT}.tsv"
#done
mdb-export -Q -d '\t' -D '%Y-%m-%d %H:%M:%S' IDB_Version_2.mdb "Tbl_MP_BASE_TREESUMMARY" > "Tbl_MP_BASE_TREESUMMARY.tsv"
