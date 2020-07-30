#!/bin/bash
# process_drawing_grid.sh
# Input: shapefile (epsg 3857) with planning grids
# Output: postgres sql file

thisdir=`dirname $BASH_SOURCE`

# Variables that change frequently/on every import
WORKING_DIR="/usr/local/apps/marineplanner-core/apps/landmapper/data"
SHP="$WORKING_DIR/ORtaxlot_allCounties.shp"
FINAL="$WORKING_DIR/OR_TAXLOTS.sql"

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
shp2pgsql -d -D -s 3857 -i -I -W LATIN1 \
    -g geometry $SHP public.landmapper_taxlot > $TMP

# Replace gid with id
sed -i 's/gid serial/id serial/' $TMP
sed -E -i 's/PRIMARY KEY \(gid\)/PRIMARY KEY \(id\)/' $TMP

# Change field names to match django model
$TRANSLATE $TMP $FIELDMAP > $FINAL

# Add a centroid geometry column in new transaction
cat << EOT >> $FINAL

BEGIN;
SELECT AddGeometryColumn('public','landmapper_taxlot','centroid','3857','POINT',2);
UPDATE "public"."landmapper_taxlot" SET "centroid" = ST_Centroid("geometry");
CREATE INDEX ON "public"."landmapper_taxlot" USING GIST ("centroid");
COMMIT;
EOT

echo "------"
echo "SUCCESS. sql file created; load into database on VM/Prod server with"
echo "psql -U postgres -d marineplanner -f $FINAL"
echo "------"
