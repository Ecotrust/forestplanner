try:
    # Local settings should probably be collected to project folder instead.
    from lot.local_settings import *
except ImportError:
    pass

try:
    from discovery.local_settings import *
except ImportError:
    pass

# This seems to help with some backward compatibility
import django
django.setup()
