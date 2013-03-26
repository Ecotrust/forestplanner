#!/bin/bash
# process_dems.sh
# Given a high-resolution DEM, derive lower res terrain rasters
# author: perrygeo@gmail.com
# Configuration:

FULLDEM="/g/Basedata/PNW/terrain/dem_prjr6/hdr.adf"
OUTDIR="resamp45"
OUTRES="45.4133849338" 
# x3 27.2480309603
# x4 36.330707947
# x5 45.4133849338

#---------------------------------------------------------------#

rm -rf $OUTDIR
mkdir $OUTDIR

NEWDEM="$OUTDIR/dem.tif"
NEWSLOPE="$OUTDIR/slope.tif"
NEWASPECT="$OUTDIR/aspect.tif"
NEWCOS="$OUTDIR/cos_aspect.tif"
NEWSIN="$OUTDIR/sin_aspect.tif"

# Resample DEM to 45 meters with integer type, tiled
gdalwarp -of GTiff -r cubic -ot Int16 \
    -co "TILED=YES" -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512" \
    -tr $OUTRES $OUTRES $FULLDEM $NEWDEM

# Create derived terrain rasters
gdaldem slope -p $NEWDEM $NEWSLOPE.float.tif -co "TILED=YES" -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512"
gdaldem aspect $NEWDEM $NEWASPECT.float.tif -co "TILED=YES" -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512"
gdal_calc.py -A $NEWASPECT.float.tif --calc "cos(radians(A))" --format "GTiff" --outfile $NEWCOS.striped.tif
gdal_calc.py -A $NEWASPECT.float.tif --calc "sin(radians(A))" --format "GTiff" --outfile $NEWSIN.striped.tif

# Convert slope and aspect to Int16
for rast in $OUTDIR/*.float.tif; do
    BASE=`echo "$rast" | cut -d'.' -f1`
    gdal_translate -ot Int16 $rast $BASE.tif -co "TILED=YES" -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512"
    rm $rast
done

# Convert cos and sin to tiled block GTiffs
for rast in $OUTDIR/*.striped.tif; do
    BASE=`echo "$rast" | cut -d'.' -f1`
    gdal_translate $rast $BASE.tif -co "TILED=YES" -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512"
    rm $rast
done

ls -alth $OUTDIR
