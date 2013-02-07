
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

package { "libmapnik":
    ensure => "installed",
    subscribe => Exec['add-apt']
}


package { "mapnik-utils":
    ensure => "installed",
    subscribe => Exec['add-apt']
}


package { "python-mapnik":
    ensure => "latest",
    subscribe => Exec['add-apt']
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

package { "python-numpy":
    ensure => "latest"
}

package { "python-scipy":
    ensure => "latest"
}


package { "python-gdal":
    ensure => "latest"
}

package { "gfortran":
    ensure => "latest"
}


package { "libopenblas-dev":
    ensure => "latest"
}


package { "liblapack-dev":
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

exec { "load postgis":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d lot",
  user => "vagrant",
  require => Postgresql::Database['lot']
}

exec { "load spatialrefs":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d lot",
  user => "vagrant",
  require => Postgresql::Database['lot']
}

python::venv::isolate { "/usr/local/venv/lot":
  subscribe => [Package['python-mapnik'], Package['build-essential']]
}

file { "settings_local.py":
  path => "/vagrant/lot/settings_local.py",
  content => template("settings_vagrant.py")

}