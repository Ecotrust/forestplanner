mdb-schema -T SPPSZ_ATTR_ALL gnn_sppsz_db.mdb postgres > schema.SPPSZ_ATTR_ALL.sql
sed -i 's/Postgres_Unknown 0x10/double precision/g' schema.SPPSZ_ATTR_ALL.sql
sed -i 's/Char/varchar/g' schema.SPPSZ_ATTR_ALL.sql
