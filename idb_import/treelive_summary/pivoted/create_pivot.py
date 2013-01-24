import pandas as pd

df = pd.read_csv("Tbl_MP_FINAL_TREELIVE_SUMMARY.csv")

print "computing pivot for TPA..."
dfpiv_tpa = df.pivot("COND_ID","VARNAME", "SumOfTPA")
dfpiv_tpa.columns = ["TPA_%s" % c for c in dfpiv_tpa.columns]

print "computing pivot for BA..."
dfpiv_ba = df.pivot("COND_ID","VARNAME", "SumOfBA_FT2_AC")
dfpiv_ba.columns = ["BA_%s" % c for c in dfpiv_ba.columns]

print "joining..."
dfpiv = pd.DataFrame.join(dfpiv_ba, dfpiv_tpa)
dfpiv.to_csv("dfpiv.tsv", sep="\t", header=False)
dfpiv.save("dfpiv.pickle")

with open("dfpiv.schema.sql",'w') as sf:
    sf.write("""DROP TABLE TREELIVE_CROSSTAB;
CREATE TABLE TREELIVE_CROSSTAB
(
  COND_ID Int8, 
%s
);
    """ % ",\n".join(["  \"%s\" Float8" % (col,) for col in dfpiv.columns]) )

