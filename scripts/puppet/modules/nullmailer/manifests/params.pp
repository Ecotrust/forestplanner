class nullmailer::params {
  case $::operatingsystem {
    /(Ubuntu|Debian)/: {
      $package = ['nullmailer', ]
      $absentpackages = [ 'exim4-daemon-light', 'exim4-daemon-heavy',
                          'postfix', 'sendmail-bin', 'citadel-mta',
                          'courier-mta', 'lsb-invalid-mta',
                          'exim4-base', 'exim4-config', 'exim4']
      $service = 'nullmailer'
      $manage_etc_mailname = true
    }
    default: {
      fail("Unsupported platform: ${::operatingsystem}")
    }
  }
}
