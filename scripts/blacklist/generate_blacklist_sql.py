# requires a 3-column csv:
# condition id, variant code, reason
#
# python generate_blacklist_sql.py > blacklist.sql
# psql -d forestplanner -U whoever -f blacklist.sql

if __name__ == "__main__":
    header = True
    for line in open("blacklist.csv").readlines():
        if header:
            header = False
            continue
        items = line.strip().split(',')
        if len(items) == 3:
            cond_id = int(items[0])
            var = items[1]
            print "--", var, cond_id
            sql = "DELETE FROM trees_fvsaggregate WHERE cond = %d AND var = '%s';" % (cond_id, var)
            print sql
            sql = "DELETE FROM trees_conditionvariantlookup WHERE cond_id = %d AND variant_code = '%s';" % (cond_id, var)
            print sql

    print "VACUUM ANALYZE;"
