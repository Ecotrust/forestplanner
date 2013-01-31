define postgresql::user($ensure=present) {
  $userexists = "/usr/bin/psql --tuples-only -c 'SELECT rolname FROM pg_catalog.pg_roles;' | grep '^ ${owner}$'"
  $user_owns_zero_databases = "/usr/bin/psql --tuples-only --no-align -c \"SELECT COUNT(*) FROM pg_catalog.pg_database JOIN pg_authid ON pg_catalog.pg_database.datdba = pg_authid.oid WHERE rolname = '${owner}';\" | grep -e '^0$'"

  if $ensure == 'present' {

    exec { "createuser $owner":
      command => "/usr/bin/createuser --superuser ${owner}",
      user    => "postgres",
      unless  => $userexists,
      require => Class["postgresql::server"],
    }

  } elsif $ensure == 'absent' {

    exec { "/usr/bin/dropuser $owner":
      command => "dropuser ${owner}",
      user => "postgres",
      onlyif => "$userexists && $user_owns_zero_databases",
    }
  }
}
