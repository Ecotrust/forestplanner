class python::gunicorn($ensure=present, $owner=undef, $group=undef) {

  $rundir = "/var/run/gunicorn"
  $logdir = "/var/log/gunicorn"

  if $ensure == "present" {
    file { [$rundir, $logdir]:
      ensure => directory,
      owner => $owner,
      group => $group,
    }

  } elsif $ensure == 'absent' {

    file { $rundir:
      ensure => $ensure,
      owner => $owner,
      group => $group,
    }
  }
}
