from forestcost import main_model
import sys
import traceback
import glob
import shutil

#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)

good = bad = 0

for txt in glob.glob("*.txt"):
    moveit = False
    with open(txt, 'r') as fh:
        lines = fh.readlines()
        args = eval(lines[6])
        try:
            main_model.cost_func(*args)
            good += 1
            moveit = True
        except:
            bad += 1
            print "-----"
            print txt
            print
            print traceback.format_exc()
    if moveit:
        shutil.move(txt, "good/" + txt)

print "##### GOOD", good
print "##### BAD", bad            


