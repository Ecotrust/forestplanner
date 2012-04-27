BASEDIR=/usr/local/apps/murdock

cd $BASEDIR/openlayers/build
cwd

python $BASEDIR/openlayers/build/build.py $BASEDIR/scripts/openlayers_lot.cfg

cp $BASEDIR/openlayers/build/OpenLayers.js $BASEDIR/media/
cd $BASEDIR/lot
cwd

python manage.py install_media
