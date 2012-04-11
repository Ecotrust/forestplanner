psql -d murdock -U murdock -f schema.SPPSZ_ATTR_ALL.sql
psql -d murdock -U murdock -c "COPY SPPSZ_ATTR_ALL FROM '/usr/local/apps/murdock/gnn_import/SPPSZ_ATTR_ALL.tsv' WITH NULL AS ''"
