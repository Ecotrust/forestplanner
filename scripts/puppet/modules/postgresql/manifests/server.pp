class postgresql::server($version="8.4",
                         $listen_addresses='localhost',
                         $max_connections=100,
                         $shared_buffers='24MB') {
  class { 'postgresql::client': 
    version => $version,
  }

  Class['postgresql::server'] -> Class['postgresql::client']

  $service_name = $operatingsystem ? {
    "Ubuntu" => "postgresql",
    default => "postgresql",
  }

  $pkgname = $operatingsystem ? {
    default => "postgresql-${version}",
  }

  package { "postgresql-${version}":
    ensure => present,
  }
  package { "postgresql-${version}-postgis":
    ensure => present,
  }
  package { "postgresql-server-dev-${version}":
    ensure => present,
  }


  File {
    owner => "postgres",
    group => "postgres",
  }

  file { "pg_hba.conf":
    path => "/etc/postgresql/${version}/main/pg_hba.conf",
    source => "puppet:///modules/postgresql/pg_hba.conf",
    mode => 640,
    require => Package[$pkgname],
  }

  file { "postgresql.conf":
    path => "/etc/postgresql/${version}/main/postgresql.conf",
    content => template("postgresql/postgresql.conf.erb"),
    require => Package[$pkgname],
  }

  service { $service_name:
    ensure => running,
    enable => true,
    hasstatus => true,
    hasrestart => true,
    subscribe => [Package[$pkgname],
                  File["pg_hba.conf"],
                  File["postgresql.conf"]],
  }
}
