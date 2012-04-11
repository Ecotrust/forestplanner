#!/bin/bash
for TT in $(mdb-tables db_template_sppsz_piece.mdb); do
    echo $TT
    mdb-export -Q -d '\t' -D '%Y-%m-%d %H:%M:%S' db_template_sppsz_piece.mdb "$TT" > "${TT}.tsv"
done
