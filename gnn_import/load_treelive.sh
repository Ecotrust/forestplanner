psql -d murdock -U murdock -f schema.TREE_LIVE.sql
psql -d murdock -U murdock -c "COPY TREE_LIVE FROM '/usr/local/apps/murdock/gnn_import/TREE_LIVE.tsv' WITH NULL AS ''"
