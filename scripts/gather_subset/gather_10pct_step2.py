counts = {
    'PN': {},
    'EC': {},
    'WC': {},
    'BM': {},
    'CA': {},
    'SO': {},
}

for line in open("matches2.csv").readlines()[1:]:
    items = line.strip().split(',')
    matched_cond = items[2]
    var = items[1]

    dd = counts[var]
    if matched_cond in dd.keys():
        dd[matched_cond] += 1
    else:
        dd[matched_cond] = 1

import operator
import math
for var in counts.keys():
    x = counts[var]
    total = sum([d[1] for d in x.items()])
    subset_hits = int(math.ceil(total * 0.50))  #
    sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1), reverse=True)

    tally = 0
    break_on_y1_change = False
    prev_y1 = 0
    for y in sorted_x:
        # if y[1] <= 2:  # only one or two matches? don't run it
        #     continue

        if y[1] != prev_y1 and break_on_y1_change:
            break

        tally += y[1]
        print "%s,%s,%s" % (var, y[0], y[1])

        if tally > subset_hits:
            break_on_y1_change = True

        prev_y1 = y[1]
