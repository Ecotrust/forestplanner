from __future__ import print_function
import os
import sqlite3
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from trees.models import FVSAggregate


def get_gyb_rows(db_path, fields, arraysize=1000):
    '''
    Fetches GYB data from the sqlite db
    yields rows as a python dict
    uses fetchmany to keep memory usage down
    '''
    sql = "SELECT {} FROM trees_fvsaggregate;".format(
        ', '.join(['"{}"'.format(x) for x in fields]))

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)

    i = 0
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            i += 1
            res = dict(result)
            # Special case, adjust semantics of offset
            # Offset from GYB is integer years
            # Offset in FP is integer in set(0,1,2,3,4) where offset=1 is 5 years, etc
            res['offset'] = int(res['offset']) / 5
            yield res
        print("inserted {} rows...".format(i))


class Command(BaseCommand):
    help = 'Imports GYB database into the fvsaggregate table'
    args = '[db_path]'

    def handle(self, *args, **options):

        try:
            db_path = args[0]
            assert os.path.exists(db_path)
        except (AssertionError, IndexError):
            raise CommandError("Specify path for gyb sqlite database (data.db)")

        # confirm that database contains a viable trees_fvsaggregate table
        gybconn = sqlite3.connect(db_path)
        gybcursor = gybconn.cursor()
        gybcursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        tables = [x[0] for x in gybcursor.fetchall()]
        if 'trees_fvsaggregate' not in tables:
            raise CommandError("trees_fvsaggregate table not found in {}".format(db_path))

        # Confirm that gyb's schema is sufficient to provide all FP schema fields
        gybcursor.execute("PRAGMA table_info(trees_fvsaggregate);")
        gyb_fieldnames = [x[1] for x in gybcursor.fetchall()]

        pgcursor = connection.cursor()
        try:
            pgcursor.execute("SELECT * FROM trees_fvsaggregate LIMIT 0;")
            # don't track id, autosequenced
            pg_fields = [desc for desc in pgcursor.description if desc[0] != 'id']
        finally:
            pgcursor.close()

        pg_fieldnames = [x[0] for x in pg_fields]

        # postgres schema is only allowed to deviate from gyb as follows...
        # special cases described in match_case function below
        assert set(pg_fieldnames) - set([x.lower() for x in gyb_fieldnames]) == set(['pp_btl', 'lp_btl'])

        pg_insert_cols = ", ".join(['"{}"'.format(f) for f in pg_fieldnames])

        def match_case(pgname):
            """return case-sensitive key name from sqlite given a postgres field name"""
            for gybfield in gyb_fieldnames:
                if pgname == gybfield.lower():
                    return gybfield
            # not present, special cases
            # If forestplanner schema calls for pp_btl or lp_btl
            # substitute PINEBTL
            if pgname == 'pp_btl':
                return "PINEBTL"
            if pgname == 'lp_btl':
                return "PINEBTL"
            raise Exception("Can't find {} in sqlite fields".format(pgname))

        gyb_values_template = ", ".join(
            ["%({})s".format(match_case(x[0])) for x in pg_fields]
        )

        query_template = """INSERT INTO trees_fvsaggregate ({})
            VALUES ({});""".format(pg_insert_cols, gyb_values_template)

        pgcursor = connection.cursor()
        try:
            with transaction.commit_on_success():
                pgcursor.executemany(query_template, get_gyb_rows(db_path, gyb_fieldnames))
        finally:
            pgcursor.close()

        print("Recaching valid_condids.")
        FVSAggregate.recache()
