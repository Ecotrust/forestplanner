#!/usr/bin/env python
# encoding: utf-8
import sys
import os
from django.core.management import call_command, execute_manager, execute_from_command_line
from django.conf import settings

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

def create_test_cmd():
    base = ['manage.py','test','--noinput','-v','2','--failfast']
    cmd_dict = base
    for app in settings.INSTALLED_APPS:
        try:
            if not app in settings.EXCLUDE_FROM_TESTS:
                cmd_dict.append(app.split(".")[-1])
        except:
            cmd_dict = base
            break
    return cmd_dict

cmd_dict = create_test_cmd()
print
print ' '.join(cmd_dict)
print
execute_from_command_line(cmd_dict)
