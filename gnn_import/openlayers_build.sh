echo
echo "Compiling openlayers to media/OpenLayers.js"
python build.py -c jsmin full.cfg ../../media/OpenLayers.js 
echo
echo "Copying images to ../../media/img"
cp -R ../img ../../media
echo
echo "Copying images to ../../media/img"
cp -R ../theme ../../media
