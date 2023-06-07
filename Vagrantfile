# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/jammy64"
  config.disksize.size = '30GB'
  config.vm.box_check_update = true
  # config.vbguest.auto_update = false if Vagrant.has_plugin?('vagrant-vbguest')

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 5432, host: 5434
  # Celery Flower
  config.vm.network "forwarded_port", guest: 5555, host: 5555

  config.vm.synced_folder "./", "/usr/local/apps/forestplanner"

  config.vm.provider "virtualbox" do |vb|
    # vb.memory = "8192" # 8GB
    vb.memory = "4096" # 4GB
    # vb.memory = "3072"
  end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   apt-get update
  #   apt-get install -y apache2
  # SHELL
end
