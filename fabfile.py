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


def install_requirements():
    run('cd %(app_dir)s && %(venv)s/bin/pip install -r ../requirements.txt' % vars)


def install_django():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py syncdb && %(venv)s/bin/python manage.py migrate && %(venv)s/bin/python manage.py install_media' % vars)
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py enable_sharing --all' % vars)
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py install_cleangeometry' % vars)


def install_media():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py install_media' % vars)


def install_data():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py import_data' % vars)


def run_server():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py runserver 0.0.0.0:8000' % vars)


# def update():
#     run('cd %(app_dir)s && git fetch && git merge origin/master' % vars)
