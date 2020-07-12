# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/bionic64"
  config.disksize.size = '15GB'
  config.vm.box_check_update = true

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 5432, host: 5433
  # Celery Flower
  config.vm.network "forwarded_port", guest: 5555, host: 5555

  config.vm.synced_folder "./", "/usr/local/apps/forestplanner"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1600"
  end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   apt-get update
  #   apt-get install -y apache2
  # SHELL
end
