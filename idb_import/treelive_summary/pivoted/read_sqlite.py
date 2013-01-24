import sqlite3
conn = sqlite3.connect('condition.sqlite')

sql = """
    SELECT COND_ID, cond."BA_Red alder_2", cond."BA_Douglas-fir_10"
    FROM cond
    WHERE (
        cond."BA_Douglas-fir_10" > 0.0
    AND cond."BA_Douglas-fir_14" > 0.0
    AND cond."BA_Red alder_2" > 0.0
    )
"""

count = 0
for row in conn.execute(sql):
    count += 1
    print row

print 
print count
