BASEDIR=/e/git

cd $BASEDIR/openlayers/build

#python $BASEDIR/openlayers/build/build.py -c none $BASEDIR/forestplanner/scripts/openlayers_lot.cfg
python $BASEDIR/openlayers/build/build.py -c jsmin $BASEDIR/forestplanner/scripts/openlayers_lot.cfg

cp $BASEDIR/forestplanner/media/OpenLayers.js $BASEDIR/forestplanner/media/OpenLayers.js.bu
cp $BASEDIR/openlayers/build/OpenLayers.js $BASEDIR/forestplanner/media/OpenLayers.js

# install media
cp $BASEDIR/forestplanner/media/OpenLayers.js $BASEDIR/forestplanner/mediaroot/OpenLayers.js

