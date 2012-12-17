psql -d murdock -U murdock -f schema.IDB.sql
psql -d murdock -U murdock -c "COPY IDB_SUMMARY FROM '/usr/local/apps/murdock/idb_import/Tbl_MP_BASE_TREESUMMARY.tsv' WITH NULL AS ''"
