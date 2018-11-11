import sys
from django.core.management import setup_environ
appdir = '/usr/local/apps/forestplanner/lot'
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from django.core import mail

print "Sending mail to mperry@ecotrust.org...",
mail.send_mail('Testing 123', 'test email ... Here is the message.',
    'forestplanner@ecotrust.org', ['mperry@ecotrust.org'],
    fail_silently=False)
print "DONE"

print "Sending mail to perrygeo@gmail.com...\n"
mail.send_mail('Testing 123', 'test email ... Here is the message.',
    'forestplanner@ecotrust.org', ['perrygeo@gmail.com'],
    fail_silently=False)
print "DONE"

print "Everything works..."
