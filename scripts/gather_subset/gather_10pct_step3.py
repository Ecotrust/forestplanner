import os
from shutil import copyfile

INDIR = "C:\\Users\\mperry\\Desktop\\Dave Walters Deliverables\\20130529\\prepped"
OUTDIR = "C:\\Users\\mperry\\Desktop\\Dave Walters Deliverables\\20130529\\prepped_subset"
DRYRUN = True
print "DRYRUN?", DRYRUN

for line in open("matches3.csv").readlines()[1:]:
    items = line.strip().split(',')

    in_base = os.path.join(INDIR, items[0], 'fvs', items[1])
    in_fvs = in_base + ".fvs"
    in_std = in_base + ".std"

    out_base = os.path.join(OUTDIR, items[0], 'fvs', items[1])
    out_fvs = out_base + ".fvs"
    out_std = out_base + ".std"

    if DRYRUN:
        print "copyfile(%s, %s)" % (in_fvs, out_fvs)
        print "copyfile(%s, %s)" % (in_std, out_std)
    else:
        copyfile(in_fvs, out_fvs)
        copyfile(in_std, out_std)
