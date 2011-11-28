#!/bin/bash
#for TT in $(mdb-tables gnn_sppsz_db.mdb); do
#    echo $TT
#    mdb-export -Q -d $'\t' -D '%%Y-%%m-%%d %%H:%%M:%%S' gnn_sppsz_db.mdb "$TT" > "gnn_sppsz_db-tsvs/${TT}.tsv"
#done
for TT in $(mdb-tables db_template_sppsz_piece.mdb); do
    echo $TT
    mdb-export -Q -d $'\t' -D '%%Y-%%m-%%d %%H:%%M:%%S' db_template_sppsz_piece.mdb "$TT" > "db_template_sppsz_piece-tsvs/${TT}.tsv"
done
