mdb-schema -T Tbl_MP_BASE_TREESUMMARY IDB_Version_2.mdb postgres > schema.IDB.sql
sed -i 's/Postgres_Unknown 0x10/double precision/g' schema.IDB.sql
sed -i 's/Char/varchar/g' schema.IDB.sql
