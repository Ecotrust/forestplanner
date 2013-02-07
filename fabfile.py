from fabric.api import * 

dev_server =  'vagrant@127.0.0.1:2222'
prod_server = []

env.forward_agent = True
env.key_filename = '~/.vagrant.d/insecure_private_key'

def dev(): 
   """ Use development server settings """
   env.hosts = [dev_server]
   
def prod():
   """ Use production server settings """ 
   env.hosts = [prod_server] 
   
   
def all(): 
   """ Use all serves """
   env.hosts = [dev_server, prod_server]


def install_requirements():
	run('cd /usr/local/apps/land_owner_tools/lot && /usr/local/venv/lot/bin/pip install -r ../requirements.txt')

def install_django():
	run('cd /usr/local/apps/land_owner_tools/lot && /usr/local/venv/lot/bin/python manage.py syncdb && /usr/local/venv/lot/bin/python manage.py migrate && /usr/local/venv/lot/bin/python manage.py install_media')	

def install_media():
	run('cd /usr/local/apps/land_owner_tools/lot && /usr/local/venv/lot/bin/python manage.py install_media')	


def run_server():
	run('cd /usr/local/apps/land_owner_tools/lot && /usr/local/venv/lot/bin/python manage.py runserver 0.0.0.0:8000')

# def update(): 
#    run('cd /usr/local/apps/land_owner_tools/lot/ && git fetch && git merge origin/master')