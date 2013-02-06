psql -d murdock -U murdock -f schema.sql
psql -d murdock -U murdock -c "COPY TREELIVE_SUMMARY FROM '/usr/local/apps/murdock/idb_import/treelive_summary/unpivoted/Tbl_MP_FINAL_TREELIVE_SUMMARY.tab' WITH NULL AS ''"
