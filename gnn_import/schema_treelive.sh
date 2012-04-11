mdb-schema -T TREE_LIVE db_template_sppsz_piece.mdb postgres > schema.TREE_LIVE.sql
sed -i 's/Postgres_Unknown 0x10/double precision/g' schema.TREE_LIVE.sql
sed -i 's/Char/varchar/g' schema.TREE_LIVE.sql
