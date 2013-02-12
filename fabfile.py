from fabric.api import *

vars = {
    'app_dir': '/usr/local/apps/land_owner_tools/lot',
    'venv': '/usr/local/venv/lot'
}

env.forward_agent = True
env.key_filename = '~/.vagrant.d/insecure_private_key'


def dev():
    """ Use development server settings """
    servers = ['vagrant@127.0.0.1:2222']
    env.hosts = servers
    return servers


def prod():
    """ Use production server settings """
    servers = []
    env.hosts = servers
    return servers


def test():
    """ Use test server settings """
    servers = []
    env.hosts = servers
    return servers


def all():
    """ Use all servers """
    env.hosts = dev() + prod() + test()


def _install_requirements():
    run('cd %(app_dir)s && %(venv)s/bin/pip install -r ../requirements.txt' % vars)


def _install_django():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py syncdb --noinput && \
                           %(venv)s/bin/python manage.py migrate --noinput && \
                           %(venv)s/bin/python manage.py install_media -a && \
                           %(venv)s/bin/python manage.py enable_sharing --all && \
                           %(venv)s/bin/python manage.py install_cleangeometry' % vars)


def create_superuser():
    """ Create the django superuser (interactive!) """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py createsuperuser' % vars)


def import_data():
    """ Fetches and installs data fixtures (WARNING: 5+GB of data; hence not checking fixtures into the repo) """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py import_data' % vars)


def init():
    """ Initialize the forest planner application """
    _install_requirements()
    _install_django()
    _install_starspan()


def runserver():
    """ Run the django dev server on port 8000 """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py runserver 0.0.0.0:8000' % vars)


def update():
    """ Sync with master git repo """
    run('cd %(app_dir)s && git fetch && git merge origin/master' % vars)
    init()


def _install_starspan():
    run('mkdir -p ~/src && cd ~/src && \
        if [ ! -d "starspan" ]; then git clone git://github.com/Ecotrust/starspan.git; fi && \
        cd starspan && \
        if [ ! `which starspan` ]; then ./configure && make && sudo make install; fi')

# TODO
# figure out line b/t puppet and fabric duties
# run test suite
# run selenium
# a "bootstrap_puppet" command to ssh into an arbitrary box, transfer files, set things up and run puppet
#  .. basically a vagrant up for non virtualbox servers

# TODO celeryd under supervisor control
"""
(lot)vagrant@precise32:/usr/local/apps/land_owner_tools$ sudo supervisorctl reload
Restarted supervisord
(lot)vagrant@precise32:/usr/local/apps/land_owner_tools$ sudo supervisorctl status
celeryd                          STARTING
(lot)vagrant@precise32:/usr/local/apps/land_owner_tools$ sudo supervisorctl restart celeryd
celeryd: stopped
celeryd: started
"""
