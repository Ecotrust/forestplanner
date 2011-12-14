export INDATA="/home/mperry/trees_test/original_data"
export OUTDATA="/home/mperry/trees_test/work"
export SCRIPTS="/home/mperry/trees_test/scripts"

if [ -d $OUTDATA ]; then
    rm -rf $OUTDATA
fi

mkdir -p $OUTDATA/inputs
mkdir -p $OUTDATA/baserx
mkdir -p $OUTDATA/offsets
mkdir -p $OUTDATA/fvs_out
mkdir -p $OUTDATA/extracted
mkdir -p $OUTDATA/scheduler_out
mkdir -p $OUTDATA/tmp


echo "======================="
echo "Step 2: stand processor"
echo "======================="
python $SCRIPTS/StandProcessor.py $INDATA/Treelist_Elliott_VEGLBL.txt $INDATA/SlfTbl_Elliott_VEGLBL.txt $OUTDATA/inputs

echo "======================="
echo "Step 3: copy baserx"
echo "======================="
cp $INDATA/BaseRx/*.key $OUTDATA/baserx/
cp -r $INDATA/BaseRx/plant $OUTDATA/baserx/plant

echo "======================="
echo "Step 4: Create Offsets"
echo "======================="
python $SCRIPTS/CreateOffsets.py $OUTDATA/baserx $OUTDATA/offsets


echo "======================="
echo "Step 5: Run G&Y"
echo "======================="
cp -r $OUTDATA/offsets/* $OUTDATA/tmp
cp -r $OUTDATA/inputs/* $OUTDATA/tmp
cp $OUTDATA/baserx/plant/*.key $OUTDATA/tmp/
cd $OUTDATA/tmp
for i in *.sh; do echo $i; 
    sh $i > log_$i.log 2> error_$i.log
    len=`wc -l error_$i.log`
    echo $len
done #; done
