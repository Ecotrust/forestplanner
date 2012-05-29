if test -z "$1"; then
	BASEDIR=/usr/local/apps/murdock
else
	BASEDIR=$1
fi


cd $BASEDIR/openlayers/build

python $BASEDIR/openlayers/build/build.py $BASEDIR/scripts/openlayers_lot.cfg

cp $BASEDIR/openlayers/build/OpenLayers.js $BASEDIR/media/
cd $BASEDIR/lot

python manage.py install_media
