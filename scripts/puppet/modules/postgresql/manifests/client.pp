class postgresql::client($version) {
  package { "postgresql-client-${version}":
    ensure => present,
  }
}
