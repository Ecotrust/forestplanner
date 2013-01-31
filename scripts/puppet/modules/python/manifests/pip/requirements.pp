# Installs packages in a requirements file for a virtualenv.
# Pip tries to upgrade packages when the requirements file changes.
define python::pip::requirements($venv, $owner=undef, $group=undef) {
  $requirements = $name
  $checksum = "$venv/requirements.checksum"

  Exec {
    user => $owner,
    group => $group,
    cwd => "/tmp",
  }

  file { $requirements:
    ensure => present,
    replace => false,
    owner => $owner,
    group => $group,
    content => "# Puppet will install packages listed here and update them if
# the the contents of this file changes.",
  }

  # We create a sha1 checksum of the requirements file so that
  # we can detect when it changes:
  exec { "create new checksum of $name requirements":
    command => "/usr/bin/sha1sum $requirements > $checksum",
    unless => "/usr/bin/sha1sum -c $checksum",
    require => File[$requirements],
  }

  exec { "update $name requirements":
    command => "$venv/bin/pip install -r $requirements",
    cwd => $venv,
    subscribe => Exec["create new checksum of $name requirements"],
    refreshonly => true,
    timeout => 36000,
  }
}
