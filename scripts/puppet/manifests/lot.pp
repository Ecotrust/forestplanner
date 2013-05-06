$user = 'vagrant'
$group = 'vagrant'
$project_dir = '/usr/local/apps/land_owner_tools'
$settings_template = 'settings_template.py.erb'
$url_base = 'http://localhost:8080'

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

package { "postfix":
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

package { "redis-server":
    ensure => "latest"
}

package {'libgeos-dev':
    ensure => "latest"
}

package {'libgdal1-dev':
    ensure => "latest"
}

package {'supervisor':
    ensure => "latest"
}

package {'uwsgi': ensure => "latest"}
package {'uwsgi-plugin-python': ensure => "latest"}
file { "forestplanner.ini":
  path => "/etc/uwsgi/apps-available/forestplanner.ini",
  content => template("forestplanner.uwsgi.ini"),
  require => [Package['uwsgi'], Package['uwsgi-plugin-python']]
}
file { "/etc/uwsgi/apps-enabled/forestplanner.ini":
   ensure => 'link',
   target => '/etc/uwsgi/apps-available/forestplanner.ini',
   require => File['forestplanner.ini']
}

package {'nginx-full': ensure => "latest"}
file {"forestplanner":
  path => "/etc/nginx/sites-available/forestplanner",
  content => template("forestplanner.nginx"),
  require => Package['nginx-full']
}
file { "/etc/nginx/sites-enabled/forestplanner":
   ensure => 'link',
   target => '/etc/nginx/sites-available/forestplanner',
   require => File['forestplanner']
}
file { "/etc/nginx/sites-enabled/default":
   ensure => 'absent',
   require => Package['nginx-full']
}

class { "postgresql::server": version => "9.1",
    listen_addresses => "'*'",  # TODO localhost',
    max_connections => 100,
    shared_buffers => '24MB',
}

postgresql::database { "forestplanner":
  owner => $user,
}

exec { "load postgis":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d forestplanner",
  user => $user,
  require => Postgresql::Database['forestplanner']
}

exec { "load spatialrefs":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d forestplanner",
  user => $user,
  require => Postgresql::Database['forestplanner']
}

exec { "load postgis template1":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d template1",
  user => "postgres",
  require => Postgresql::Database['forestplanner']
}

exec { "load spatialrefs template1":
  command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d template1",
  user => "postgres",
  require => Postgresql::Database['forestplanner']
}

exec { "load cleangeometry template1":
  command => "/usr/bin/psql -d template1 -f $project_dir/scripts/puppet/manifests/files/cleangeometry.sql",
  user => "postgres",
  require => Postgresql::Database['forestplanner']
}

python::venv::isolate { "/usr/local/venv/lot":
  subscribe => [Package['python-mapnik'], Package['build-essential']]
}

file { "settings_local.py":
  path => "$project_dir/lot/settings_local.py",
  content => template($settings_template)
}

file { "go":
  path => "/home/$user/go",
  content => template("go"),
  owner => $user,
  group => $group,
  mode => 0775
}

file { "celeryd.conf":
  path => "/etc/supervisor/conf.d/celeryd.conf",
  content => template("celeryd.erb"),
  require => Package['supervisor']
}
file { "celerymon.conf":
  path => "/etc/supervisor/conf.d/celerymon.conf",
  content => template("celerymon.erb"),
  require => Package['supervisor']
}
file { "celeryflower.conf":
  path => "/etc/supervisor/conf.d/celeryflower.conf",
  content => template("celeryflower.erb"),
  require => Package['supervisor']
}