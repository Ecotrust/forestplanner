class nullmailer::package {
  package { $nullmailer::package:
    ensure => present,
  }

  package { $nullmailer::absentpackages:
    ensure => absent,
  }
}
