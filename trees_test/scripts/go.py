from StandProcessor import StandProcessor
from CreateOffsets import create_offsets
from glob import glob
import os
import sys
import shutil
import subprocess

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
INDATA = os.path.join(ROOT, "original_data")
OUTDATA = os.path.join(ROOT, "work")
SCRIPTS = os.path.join(ROOT, "scripts")
FVSBIN = "/usr/local/FVSbin/FVSpn.exe"

treelist_file = os.path.join(INDATA, 'Treelist_Elliott_VEGLBL.txt')
pre_slf_file = os.path.join(INDATA, 'SlfTbl_Elliott_VEGLBL.txt')


def first():
    print "======================="
    print "Step 1: set up dirs"
    print "======================="
    if os.path.exists(OUTDATA):
        shutil.rmtree(OUTDATA)
        os.makedirs(OUTDATA)

    subdirs = ['inputs', 'offsets', 'fvs_out', 'extract', 'scheduler_out', 'tmp']
    for sd in subdirs:
        os.makedirs(os.path.join(OUTDATA, sd))

    print "======================="
    print "Step 2: stand processor"
    print "======================="
    sp = StandProcessor()
    sp.create_stand_files(treelist_file, pre_slf_file, os.path.join(OUTDATA,'inputs'))

    print "======================="
    print "Step 3: copy baserx"
    print "======================="
    shutil.copytree(os.path.join(INDATA,'BaseRx'), os.path.join(OUTDATA,'baserx'))

    print "======================="
    print "Step 4: Create Offsets"
    print "======================="
    create_offsets(os.path.join(OUTDATA,'baserx'), os.path.join(OUTDATA, 'offsets'), num_offsets = 9, period = 5) 


    print "======================="
    print "Step 5: Run G&Y"
    print "======================="
    # First copy stuff to tmp
    tmp = os.path.join(OUTDATA, 'tmp')
    for i in glob(os.path.join(OUTDATA, 'inputs', '*')):
        shutil.copy(i, tmp)
    for o in glob(os.path.join(OUTDATA,'offsets','*')):
        shutil.copy(o, tmp)
    os.chdir(tmp)

    # Get the keys
    keys = glob('*.key')
    keys.sort()

    # Now copy the plant keys
    for k in glob(os.path.join(OUTDATA,'baserx','plant','*.key')):
        shutil.copy(k, tmp)

    for key in keys:
        key = key.replace(".key","")
        print
        print key
        rsp_fh = open(key + '.rsp', 'w')
        lines = """%(outbase)s.key
%(outbase)s.tre
%(outbase)s.out
%(outbase)s.trl
%(outbase)s.sum
%(outbase)s.chp""" % {'outbase': key}
        rsp_fh.write(lines)
        rsp_fh.close()

        cmd = "cat %(outbase)s.rsp | wine %(fvsbin)s" % {'outbase': key, 'fvsbin': FVSBIN}   
        print cmd
        proc = subprocess.Popen(cmd, shell=True,
                    #stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE)
        out, err = proc.communicate()
        returncode = proc.returncode
        if returncode > 0:
            print "============"
            print returncode
            print err
            print "============"
            raise Exception("FVS Failed with returncode %s..." % returncode)

def second():
    print "======================="
    print "Step 6: Run extraction scripts"
    print "======================="

    tmp = os.path.join(OUTDATA, 'tmp')
    treelist_prefixes = ['alt', 'bus']
    extract_scripts = [
            'gy_age_extract.pl',
            'gy_carbon_extract.pl',
            'gy_cut_extract.pl',
            'gy_live_extract.pl'
    ]


    for prefix in treelist_prefixes:
        ### Copy and set up files
        # Question: which Rxs do we copy?
        # maybe do symlinks here?
        treelist_dir = os.path.join(OUTDATA, 'extract','%s_treelists' % prefix)
        if os.path.exists(treelist_dir):
            shutil.rmtree(treelist_dir)
        os.makedirs(treelist_dir)
        for i in glob(os.path.join(tmp, '*.trl')):
            shutil.copy(i, treelist_dir)
        for i in glob(os.path.join(tmp, '*.out')):
            shutil.copy(i, treelist_dir)

        for script in extract_scripts:
            extract_dir = os.path.join(OUTDATA, 'extract')
            shutil.copy(os.path.join(SCRIPTS, 'init.cfg'), extract_dir)
            shutil.copy(os.path.join(SCRIPTS, script), extract_dir)
            os.chdir(extract_dir)

            cmd = "perl %s %s" % (script, prefix)
            print cmd
            proc = subprocess.Popen(cmd, shell=True,
                        #stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
            out, err = proc.communicate()
            returncode = proc.returncode
            if returncode > 0:
                print "============"
                print returncode
                print err
                print "============"
                raise Exception("Extract Script Failed with returncode %s..." % returncode)

    print "======================="
    print "Step 7: Determine adjaceny"
    print "======================="
    print
    print "TBD...."
    print "Just copy one over for now"
    print

    print "======================="
    print "Step 8: Run scheduler"
    print "======================="


if __name__ == "__main__":
    first()
    second()
