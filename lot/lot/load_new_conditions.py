import os, sys
os.environ['DJANGO_SETTINGS_MODULE']='settings'
# import django
# import settings
from trees.plots import *
import csv
from trees.models import TreeliveSummary, ConditionVariantLookup
import ipdb
import datetime
import gc

# NEW_CVLU_FILE="../docs/New_NN/COND_VAR_Lookup.csv"
# NEW_TLSUM_FILE="../docs/New_NN/TREELIVE_SUMMARY_2015-11-19.csv"
NEW_TLSUM_FILE="../docs/New_NN/TREELIVE_SUMMARY_2015-12-15.csv"

# print 'please truncate the ConditionVariantLookup table using a database tool now. Press c to continue'
# ipdb.set_trace()
# print "Importing new condition variant lookup table"
# with open(NEW_CVLU_FILE, 'rb') as cvlu:
#     reader = csv.DictReader(cvlu)
#     for row in reader:
#         try:
#             (lookup, created) = ConditionVariantLookup.objects.get_or_create(
#                 cond_id=row['COND_ID'],
#                 variant_code=row['FVSVARIANT']
#             )
#         except:
#             print "ERROR: On row - %s" % str(row)

# print 'please truncate the TreeliveSummary table using a database tool now. Press c to continue'
# ipdb.set_trace()
print 'Importing new treelive summary file'
done = False
terminated = False
error = False
if len(sys.argv) >= 2 and sys.argv[1].isdigit():
    start_index = int(sys.argv[1])
else:
    # import ipdb
    # ipdb.set_trace()
    print "ERROR: Incorrect arguments passed: %s" % str(sys.argv)
    # return(False, False, True, index)
    sys.exit(1)
    # start_index = 3770000
def import_csv(start_index):
    start = datetime.datetime.now()
    with open(NEW_TLSUM_FILE, 'rb') as tlsum:
        reader = csv.DictReader(tlsum)
        for index, row in enumerate(reader):
            # if index > 1200000:
            if index > start_index:
                try:
                    (treeSum, created) = TreeliveSummary.objects.get_or_create(
                        class_id=int(row['class_id']),
                        plot_id=int(row['plot_id']),
                        cond_id=int(row['cond_id']),
                        variant = row['variant'],
                        varname = row['varname'],
                        fia_forest_type_name=row['fia_forest_type_name'],
                        fvs_spp_code = row['FVS_Spp_Code'],
                        calc_dbh_class=int(float(row['calc_dbh_class'])),
                        calc_tree_count = int(row['calc_tree_count']),
                        sumoftpa = float(row['sumoftpa']),
                        avgoftpa = float(row['avgoftpa']),
                        sumofba_ft2_ac = float(row['sumofba_ft2_ac']),
                        avgofba_ft2_ac = float(row['avgofba_ft2_ac']),
                        avgofht_ft = float(row['avgofht_ft']),
                        avgofdbh_in = float(row['avgofdbh_in']),
                        avgofage_bh = float(row['avgofage_bh']) if not row['avgofage_bh'] == '' else None,
                        total_ba_ft2_ac = float(row['total_ba_ft2_ac']),
                        count_speciessizeclasses = int(row['count_speciessizeclasses']),
                        pct_of_totalba = float(row['pct_of_totalba'])
                    )

                    if index > 0 and index % 10000 == 0:
                        loop_end = datetime.datetime.now()
                        loop_time = loop_end - start
                        print "%s records done. Rate: %s/second -- %s" % (str(index), str(10000/loop_time.total_seconds()), loop_end.timetz().isoformat())
                        gc.collect()
                        # print str(loop_time.total_seconds())
                        if loop_time.total_seconds() > 90:
                            # print 'Too slow! Halting for restart at row %s, %s' % (str(index), loop_end.timetz().isoformat())
                            # print '%s' % str(index)
                            gc.collect()
                            # break
                            # print "%s" % str(index)
                            # sys.exit(0)

                            return (False, True, False, index)
                        # else:
                        #     import ipdb
                        #     ipdb.set_trace()

                        start = datetime.datetime.now()
                    # if index >= 4000:
                    #     break
                except:
                    # import ipdb; ipdb.set_trace()
                    print "ERROR: On row - %s" % str(row)
                    return (False, False, True, index)
    return (True, False, False, index)

while not done and not terminated and not error:
    (done, terminated, error, start_index) = import_csv(start_index)

if terminated:
    print "%s" % start_index
if done:
    # print 'Complete! %s records inserted.' % str(start_index)
    print 'done'
if error:
    sys.exit(1)
#     print "ERROR: Near %s" % str(start_index)
sys.exit(0)
