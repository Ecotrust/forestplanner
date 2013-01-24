import pandas as pd
import sqlite3
from pandas.io import sql

print "importing treelive..."
treelive = pd.read_csv("Tbl_MP_FINAL_TREELIVE_SUMMARY.csv")
treelive = treelive[:32002]

print "computing pivot for TPA..."
dfpiv_tpa = treelive.pivot("COND_ID","VARNAME", "SumOfTPA")
dfpiv_tpa.columns = ["TPA_%s" % c for c in dfpiv_tpa.columns]

print "computing pivot for BA..."
dfpiv_ba = treelive.pivot("COND_ID","VARNAME", "SumOfBA_FT2_AC")
dfpiv_ba.columns = ["BA_%s" % c for c in dfpiv_ba.columns]

print "importing base..."
base = pd.read_csv("Tbl_MP_BASE_TREESUMMARY.csv")

print "joining pivot tables..."
dfpiv = pd.DataFrame.join(dfpiv_ba, dfpiv_tpa)

print "joining to base table..."
final = base.join(dfpiv, on="COND_ID", how="inner")

print "Writing to sqlite..."
conn = sqlite3.connect('condition.sqlite')
sql.write_frame(final, name='cond', con=conn)

