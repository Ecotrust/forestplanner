class python::venv($ensure=present, $owner=undef, $group=undef) {

  package { "python-virtualenv":
    ensure => $ensure,
  }
}
