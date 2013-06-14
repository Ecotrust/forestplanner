Puppet module for nullmailer
============================

Nullmailer is useful in situations where you have machines but do not wish
to configure them with a full email service (mail transfer agent, MTA).

Particularly to send email about local activity to a centralised place.

By default, the module will configure things to be sent, via SMTP, to the machine:

	smtp.$::domain

and then to the address:

	root@$::domain

i.e. given $::domain is 'example.com', mail would be sent to
root@example.com via SMTP to smtp.example.com

This may require you to configure your SMTP server to accept
incoming email from various machines.

NOTE: /etc/mailname must be set to a reasonable value. This
module will, by default, set it to $::fqdn

Basic usage
-----------

    class {'nullmailer':  }

To configure who will receive all email:

    class {'nullmailer':
        adminaddr => "puppet-rockstar@example.com"
    }

Or to change the machine where email is sent to:

    class {'nullmailer':
        remoterelay => "elsewhere.example.com"
    }

When modifying these parameters, please ensure the value is in
double quotes.

Other things to modify are listed in the init.pp file

Advanced usage
---------------

nullmailer is also able to use a remote relay which is on a different port, requires authentication, etc.

As the combination of options will vary widely between various setups, instead a 'remoteopts' variable is provided.

    class {'nullmailer':
        remoteopts => "--port=2525"
    }

Send to port 2525 instead of port 25

    class {'nullmailer':
        remoteopts => "--user=foo --pass=bar"
    }

Other available options (for Nullmailer 1.10+) are:

- --port, set the port number of the remote host to connect to
- --user, set the user name to be used for authentication
- --pass, set the password for authentication
- --auth-login, use AUTH LOGIN instead of auto-detecting in SMTP
- --ssl, Connect using SSL (on port 465 instead) (1.10+)
- --starttls, use STARTTLS command (1.10+)
- --x509cafile, Certificate authority trust file (1.10+)
- --x509crlfile, Certificate revocation list file (1.10+)
- --x509fmtdef, X.509 files are in DER format (1.10+)
- --insecure, Do not abort if server certificate fails validation (1.10+)

Another use case might be *not* rewriting, or even having, a specific
admin address to send email to. In this case, set adminaddr to the
magic value of an empty string, like so;

    class {'nullmailer':
        adminaddr => '',
    }

With things set up like this the remoterelay decides what addresses
will be rewritten rather than all of them being rewritten at the client
prior to sending.

Notes
-----

nullmailer is capable of handling multiple remote SMTP servers for delivery.
If this is your setup, this module will not work out of the box for you.

Contributors
------------

 * [Anand Kumria](https://github.com/akumria) ([@akumria](https://twitter.com/akumria))
 * [Callum Macdonald](https://github.com/chmac)
 * [Arne Schwabe](https://githib.com/schwabe)
 * [Klaus Ethgen](https://github.com/mowgli)


Copyright and License
---------------------

Copyright 2012-2013 [Linuxpeak](https://www.linuxpeak.com/) Pty Ltd.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
