BASEDIR=/e/git

cd $BASEDIR/openlayers/build

#python $BASEDIR/openlayers/build/build.py -c none $BASEDIR/land_owner_tools/scripts/openlayers_lot.cfg
python $BASEDIR/openlayers/build/build.py -c jsmin $BASEDIR/land_owner_tools/scripts/openlayers_lot.cfg

cp $BASEDIR/land_owner_tools/media/OpenLayers.js $BASEDIR/land_owner_tools/media/OpenLayers.js.bu
cp $BASEDIR/openlayers/build/OpenLayers.js $BASEDIR/land_owner_tools/media/OpenLayers.js

# install media
cp $BASEDIR/land_owner_tools/media/OpenLayers.js $BASEDIR/land_owner_tools/mediaroot/OpenLayers.js

