#!/bin/bash
# process_drawing_grid.sh
# Input: shapefile (epsg 3857) with planning grids
# Output: postgres sql file

thisdir=`dirname $BASH_SOURCE`

# Variables that change frequently/on every import
WORKING_DIR="/usr/local/apps/forestplanner/lot/landmapper/data/taxlots_2021"
SHP="$WORKING_DIR/taxlot.shp"
FINAL="$WORKING_DIR/OR_TAXLOTS_2021.sql"

SRID=3857
table_name='landmapper_taxlot'
database_name='disco'
db_user='postgres'

################################################################################
# Probably no need to touch anything below here
################################################################################

# Path will not change by json file may need to be updated
FIELDMAP="$thisdir/taxlot_field_map.json"

# Probably won't need to touch these if running from root project dir
TMP="$WORKING_DIR/taxlot_planning_grid.sql"
TRANSLATE="python $thisdir/translate.py"
VALIDATE="python $thisdir/validate_fields.py"

# Do some sanity checks on the fieldnames
#$VALIDATE $SHP $FIELDMAP
#if [ $? -ne 0 ]; then
#    echo "NOT VALID"
#    exit 1
#fi

# export shp to dump format sql
# -d option handles dropping table before creation
# -g option specifies geometry column name
shp2pgsql -k -d -D -s $SRID -i -I -W LATIN1 \
    -g geometry $SHP public.$table_name > $TMP

# Replace gid with id
sed -i 's/gid serial/id serial/' $TMP
sed -E -i 's/PRIMARY KEY \(gid\)/PRIMARY KEY \(id\)/' $TMP

# Change field names to match django model
$TRANSLATE $TMP $FIELDMAP > $FINAL

# Add a centroid geometry column in new transaction
cat << EOT >> $FINAL

BEGIN;
SELECT AddGeometryColumn('public','$table_name','centroid','$SRID','POINT',2);
UPDATE "public"."$table_name" SET "centroid" = ST_Centroid("geometry");
CREATE INDEX ON "public"."$table_name" USING GIST ("centroid");
COMMIT;
EOT

echo "------"
echo "SUCCESS. sql file created; load into database on VM/Prod server with"
echo "psql -U $db_user -d $database_name -f $FINAL"
echo "------"
