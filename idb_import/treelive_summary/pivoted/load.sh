psql -d murdock -U murdock -f dfpiv.schema.sql
psql -d murdock -U murdock -c "COPY TREELIVE_CROSSTAB FROM '/usr/local/apps/murdock/idb_import/treelive_summary/dfpiv.tsv' WITH NULL AS ''"
