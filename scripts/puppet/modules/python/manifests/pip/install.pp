define python::pip::install($package, $venv, $ensure=present,
                            $owner=undef, $group=undef) {

  # Match against whole line if we provide a given version:
  $grep_regex = $package ? {
    /==/ => "^${package}\$",
    default => "^${package}==",
  }

  Exec {
    user => $owner,
    group => $group,
    cwd => "/tmp",
  }

  if $ensure == 'present' {
    exec { "pip install $name":
      command => "$venv/bin/pip install $package",
      unless => "$venv/bin/pip freeze | grep -e $grep_regex"
    }
  } elsif $ensure == 'latest' {
    exec { "pip install $name":
      command => "$venv/bin/pip install -U $package",
    }
  } else {
    exec { "pip install $name":
      command => "$venv/bin/pip uninstall $package",
      onlyif => "$venv/bin/pip freeze | grep -e $grep_regex"
    }
  }
}
