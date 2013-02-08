import os
from django.core.management.base import BaseCommand, AppCommand, CommandError
from django.core.management import call_command
from optparse import make_option
from django.conf import settings
from django.contrib.auth.models import User
from trees.models import Stand, ForestProperty, IdbSummary, TreeliveSummary
import requests
import tempfile

class Command(BaseCommand):
    help = 'Download and load essential datasets'
    args = '[type]'

    def get_tempfile(self, url, suffix=""):
        "get file, save to temp, returns temp filepath"
        rq = requests.get(url)
        tf = tempfile.NamedTemporaryFile(suffix=suffix)
        tf.write(rq.content)
        tf.file.flush()
        return tf

    def handle(self, *args, **options):
        if IdbSummary.objects.all().count() == 0:
            print "Getting IdbSummary data"
            with self.get_tempfile("http://labs.ecotrust.org/forestplanner/data/idbsummary.json.gz", suffix=".json.gz") as tf:
                call_command('loaddata', tf.name)
        else:
            print "Skipping IdbSummary data"

        if TreeliveSummary.objects.all().count() == 0:
            print "Getting TreeliveSummary data"
            with self.get_tempfile("http://labs.ecotrust.org/forestplanner/data/treelivesummary.json.gz", suffix=".json.gz") as tf:
                call_command('loaddata', tf.name)
        else:
            print "Skipping TreeliveSummary data"
