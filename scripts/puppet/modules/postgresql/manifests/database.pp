define postgresql::database($owner, $ensure=present) {
  $dbexists = "/usr/bin/psql -ltA | grep '^$name|'"
  $postgisexists = "/usr/bin/psql -c 'SELECT tablename FROM pg_tables' $name | grep '^\$geography_columns|'"
  
  postgresql::user { $owner:
    ensure => $ensure,
  }

  if $ensure == 'present' {

    exec { "createdb":
      command => "/usr/bin/createdb -O $owner $name",
      user => "postgres",
      unless => $dbexists,
      require => Postgresql::User[$owner],
    }

    exec { "load postgis $name":
      command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d $name",
      user => $owner,
      onlyif => $dbexists,
      require => Postgresql::User[$owner],
      subscribe => Exec['createdb']
    }

    exec { "load spatialrefs $name":
      command => "/usr/bin/psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d $name",
      user => $owner,
      onlyif => $dbexists,
      require => Postgresql::User[$owner],
      subscribe => Exec['createdb']
    }

  } elsif $ensure == 'absent' {

    exec { "dropdb $name":
      command => "/usr/bin/dropdb $name",
      user => "postgres",
      onlyif => $dbexists,
      before => Postgresql::User[$owner],
    }
  }
}
