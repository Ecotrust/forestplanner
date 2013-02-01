
# ensure that apt update is run before any packages are installed
class apt {
  exec { "apt-update":
    command => "/usr/bin/apt-get update"
  }

  # Ensure apt-get update has been run before installing any packages
  Exec["apt-update"] -> Package <| |>

}


include apt

exec { "add-apt":
  command => "/usr/bin/add-apt-repository -y ppa:mapnik/nightly-2.0 && /usr/bin/apt-get update",
  subscribe => Package["python-software-properties"]
}


package { "build-essential":
    ensure => "installed"

}

package { "python-software-properties":
    ensure => "installed"

}

package { "git-core":
    ensure => "latest"
}

package { "subversion":
    ensure => "latest"
}

package { "mercurial":
    ensure => "latest"
}

package { "csstidy":
    ensure => "latest"
}

package { "vim":
    ensure => "latest"
}

package { "python-psycopg2":
    ensure => "latest"
}

package { "python-virtualenv":
    ensure => "latest"
}

package { "python-dev":
    ensure => "latest"
}

class { "postgresql::server": version => "9.1",
    listen_addresses => 'localhost',
    max_connections => 100,
    shared_buffers => '24MB',
}

postgresql::database { "lot":
  owner => "vagrant",
}

python::venv::isolate { "/usr/local/venv/lot":
  requirements => "/vagrant/requirements.txt",
  subscribe => [Package['python-mapnik'], Package['build-essential']]
}

#exec { "Django Syncdb":
#  path => "/bin:/usr/bin",
#  command => "/usr/local/venv/digitaldeck/bin/python /vagrant/digitaldeck/manage.py --noinput syncdb"
#}

#exec { "Django Migrate":
#  path => "/bin:/usr/bin",
#  command => "/usr/local/venv/digitaldeck/bin/python /vagrant/digitaldeck/manage.py migrate",
#  subscribe => Exec['Django Syncdb']
#}
