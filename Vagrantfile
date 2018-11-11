# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "precise64"

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  #config.vm.customize ["modifyvm", :id, "--cpus", 2]
  config.vm.customize ["modifyvm", :id, "--memory", 898]

  # Boot with a GUI so you can see the screen. (Default is headless)
  # config.vm.boot_mode = :gui

  # Assign this VM to a host-only network IP, allowing you to access it
  # via the IP. Host-only networks can talk to the host machine as well as
  # any other machines on the same network, but cannot be accessed (through this
  # network interface) by any external networks.
  # config.vm.network :hostonly, "192.168.33.10"

  # Assign this VM to a bridged network, allowing you to connect directly to a
  # network using the host's network device. This makes the VM appear as another
  # physical device on your network.
  # config.vm.network :bridged

  # Forward a port from the guest to the host, which allows for outside
  # computers to access the VM, whereas host only networking does not.
  config.vm.forward_port 80, 8080
  config.vm.forward_port 443, 8443
  config.vm.forward_port 8000, 8000
  config.vm.forward_port 5432, 5433

  # Share an additional folder to the guest VM. The first argument is
  # an identifier, the second is the path on the guest to mount the
  # folder, and the third is the path on the host to the actual folder.
  config.vm.share_folder "v-app", "/usr/local/apps/forestplanner", "./", mount_options: ["dmode=775,fmode=664"]

  # To use a local copy of madrona:
  if File.directory?("../madrona")
    config.vm.share_folder "v-madrona", "/usr/local/src/madrona", "../madrona", mount_options: ["dmode=775,fmode=664"]
    # then vagrant ssh,
    #   source /usr/local/venv/lot/bin/activate
    #   pip uninstall madrona
    #   cd /usr/local/src/madrona
    #   python setup.py develop
  end

  if File.directory?("../cost_model")
    config.vm.share_folder "v-cost-model", "/usr/local/apps/cost_model", "../cost_model", mount_options: ["dmode=775,fmode=664"]
  end

  if File.directory?("../harvest-scheduler")
    config.vm.share_folder "v-harvest-scheduler", "/usr/local/apps/harvest-scheduler", "../harvest-scheduler", mount_options: ["dmode=775,fmode=664"]
  end

  # Enable provisioning with Puppet stand alone.  Puppet manifests
  # are contained in a directory path relative to this Vagrantfile.
  # You will need to create the manifests directory and a manifest in
  # the file (.pp) in the manifests_path directory.

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "scripts/puppet/manifests"
    puppet.manifest_file  = "lot.pp"
    puppet.module_path = "scripts/puppet/modules"
    puppet.options = ["--templatedir","/vagrant/scripts/puppet/manifests/files"]
  end

end
