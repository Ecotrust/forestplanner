import glob
import sys
import os
import shutil

def log(x):
    print x

FVSBIN = "/home/mperry/FVSbin/FVSpn.exe"

def create_offsets(baserxdir, outdir, num_offsets=10, period=5):
    for inkey in glob.glob(os.path.join(baserxdir, '*.key')):
        keyprefix = os.path.splitext(os.path.basename(inkey))[0]
        keybase = keyprefix.split('_')[0]
        # GO = grow only = a special case
        if keybase == "GO":
            continue
        log("Processing %s keys" % keybase)

        # Create XX_01.key
        outkey = os.path.join(outdir, keybase + "_01.key")
        shutil.copy(inkey, outkey)
        log("  base key %s_01.key" % keybase)

        for offset in range(2,num_offsets):
            log("  offset key %s" % offset)
            offset_years = (offset - 1) * period
            # Create the XX_YY.key offsets
            outkey = os.path.join(outdir, "%s_%02d.key" % (keybase, offset))
            ofh = open(outkey, 'w')
            for line in open(inkey,'r'):
                newline = line
                if line.startswith("Offset ="):
                    newline = "Offset = %d\r\n" % offset_years
                ofh.write(newline)
            ofh.close()


        # Create final key; grow only
        gokey = os.path.join(baserxdir, "GO_01.key")
        outkey = os.path.join(outdir, "%s_%02d.key" % (keybase, num_offsets))
        shutil.copy(gokey, outkey)
        log("  grow-only key GO_%s.key" % num_offsets)



if __name__ == "__main__":
    if len(sys.argv) == 3:
        create_offsets(sys.argv[1], sys.argv[2], num_offsets=9)
    else:
        raise Exception
