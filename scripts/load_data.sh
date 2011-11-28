psql -d murdock -U murdock -f CREATE_tree_live.sql
psql -d murdock -U murdock -c "COPY TREE_LIVE FROM '/usr/local/apps/murdock/data/gnn/tsvs/TREE_LIVE.tsv' WITH NULL AS ''"
