class python::dev($ensure=present, $version=latest) {

  $python = $version ? {
    'latest' => "python",
    default => "python${version}",
  }

  # python-dev packages depends on the correct python package in Debian:
  package { "${python}-dev":
    ensure => $ensure,
  }
}
