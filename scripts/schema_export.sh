mdb-schema -T TREE_LIVE databases/db_template_sppsz_piece.mdb postgres > /tmp/table.schema
sed 's/Postgres_Unknown 0x10/double precision/g' /tmp/table.schema | sed 's/Char/varchar/g'

