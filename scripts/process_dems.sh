FULLDEM="terrain/dem_swor2/"
OUTDIR="resamp45"

########################

rm -rf $OUTDIR
mkdir $OUTDIR

NEWDEM="$OUTDIR/dem.tif"
NEWSLOPE="$OUTDIR/slope.tif"
NEWASPECT="$OUTDIR/aspect.tif"
NEWCOS="$OUTDIR/cos_aspect.tif"
NEWSIN="$OUTDIR/sin_aspect.tif"

# Resample DEM to 45 meters with integer type, tiled
gdalwarp -of GTiff -r cubic -ot Int16 -co "TILED=YES" \
    -co "BLOCKYSIZE=512" -co "BLOCKXSIZE=512" \
    -tr 45 45 $FULLDEM $NEWDEM

gdaldem slope -p $NEWDEM $NEWSLOPE
gdaldem aspect $NEWDEM $NEWASPECT
gdal_calc.py -A $NEWASPECT --calc "cos(radians(A))" --format "GTiff" --outfile $NEWCOS
gdal_calc.py -A $NEWASPECT --calc "sin(radians(A))" --format "GTiff" --outfile $NEWSIN

ls -alth $OUTDIR
