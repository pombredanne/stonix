###############################################################################
#                                                                             #
# Copyright 2015.  Los Alamos National Security, LLC. This material was       #
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos    #
# National Laboratory (LANL), which is operated by Los Alamos National        #
# Security, LLC for the U.S. Department of Energy. The U.S. Government has    #
# rights to use, reproduce, and distribute this software.  NEITHER THE        #
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY,        #
# EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  #
# If software is modified to produce derivative works, such modified software #
# should be clearly marked, so as not to confuse it with the version          #
# available from LANL.                                                        #
#                                                                             #
# Additionally, this program is free software; you can redistribute it and/or #
# modify it under the terms of the GNU General Public License as published by #
# the Free Software Foundation; either version 2 of the License, or (at your  #
# option) any later version. Accordingly, this program is distributed in the  #
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the     #
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    #
# See the GNU General Public License for more details.                        #
#                                                                             #
###############################################################################

Name: stonix
Summary: Cross platform hardening tool for *NIX platforms
Version: 0.9.4
Release: 0%{dist}
License: GPL v. 2.0
Group: System administration tools
Source0: %{name}-%{version}.tgz
BuildRoot: %{_builddir}/%{name}-%{version}-%{release}-root
Requires: python, curl
BuildArch: noarch

%description
STONIX: The Security Tool for *NIX. STONIX is designed to harden and configure Unix/linux installations to USGCB/CIS/NSA/DISA STIG standards. 

%prep
%setup -q
%build
%install
mkdir -p $RPM_BUILD_ROOT/etc
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/usr/bin/stonix_resources
mkdir -p $RPM_BUILD_ROOT/usr/bin/stonix_resources/rules
mkdir -p $RPM_BUILD_ROOT/usr/bin/stonix_resources/gfx
mkdir -p $RPM_BUILD_ROOT/usr/bin/stonix_resources/files
mkdir -p $RPM_BUILD_ROOT/usr/share/man/man8

/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/stonix_resources/*.py $RPM_BUILD_ROOT/usr/bin/stonix_resources/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/stonix_resources/rules/*.py $RPM_BUILD_ROOT/usr/bin/stonix_resources/rules/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/stonix_resources/gfx/* $RPM_BUILD_ROOT/usr/bin/stonix_resources/gfx/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/stonix_resources/files/* $RPM_BUILD_ROOT/usr/bin/stonix_resources/files/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/usr/share/man/man8/stonix.8 $RPM_BUILD_ROOT/usr/share/man/man8/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/stonix.py $RPM_BUILD_ROOT/usr/bin/
touch $RPM_BUILD_ROOT/etc/stonix.conf

pushd $RPM_BUILD_ROOT/usr/bin
ln -s stonix.py stonix
popd

mkdir -p $RPM_BUILD_ROOT/var/www/html/stonix/results/
mkdir -p $RPM_BUILD_ROOT/var/local/stonix-server/
mkdir -p $RPM_BUILD_ROOT/usr/sbin
mkdir -p $RPM_BUILD_ROOT/usr/share/stonix/diffdir
mkdir -p $RPM_BUILD_ROOT/usr/share/stonix/archive
mkdir -p $RPM_BUILD_ROOT/usr/share/stonix
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/LogImporter/stonixImporter.py $RPM_BUILD_ROOT/usr/sbin/
/usr/bin/install $RPM_BUILD_DIR/%{name}-%{version}/LogImporter/results.php $RPM_BUILD_ROOT/var/www/html/stonix/


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr (755,root,root)
/usr/bin/stonix
/usr/bin/stonix.py
/usr/bin/stonix_resources/


%config(noreplace) %attr(0644,root,root) /etc/stonix.conf
%doc %attr(0644,root,root) /usr/share/man/man8/stonix.8.gz


%dir %attr(0755,root,root) /usr/bin/stonix_resources
%dir %attr(0700,root,root) /usr/share/stonix/diffdir
%dir %attr(0700,root,root) /usr/share/stonix/archive
%dir %attr(0700,root,root) /usr/share/stonix
%dir %attr(0755,root,root) /usr/share/man
%dir %attr(0755,root,root) /usr/share/man/man8

%post

%postun

%package importer
Summary: Stonix report importer component
Group: System Environment/Applications
Requires: python, MySQL-python
%description importer
The stonix importer program is expected to run from cron and is used to import
stonix report logs into a properly prepared MySQL database. The cron job is not
automatically established. The SQL statements to create the MySQL database are
installed at /usr/local/stonix/stonixdb.sql

%files importer
%defattr (755,root,root)
%dir %attr(0700,root,root) /var/local/stonix-server/
%dir %attr(0750,root,apache) /var/www/html/stonix/
%dir %attr(0775,root,apache) /var/www/html/stonix/results
%attr(0750,root,root) /usr/sbin/stonixImporter.py
%attr(0750,root,apache) /var/www/html/stonix/results.php

%changelog
* Thu Feb 4 2016 David Kennel <dkennel@lanl.gov> - 0.9.4
- Fixed issue where filehelper object did not configure statechglogger correctly when the file to be removed does not exist
- New rule for OS X - ConfigureDiagnosticReporting
- SetSScorners enabled for OS X 10.11
- Corrected index errors in ConfigureDotFiles rule
- Refactor of the SecureMTA rule
- Multiple fixes to unit tests
- Correction of NCAF condition in DisableCamera on OS X 10.11

* Mon Dec 21 2015 David Kennel <dkennel@lanl.gov> - 0.9.3
- Clarified Kerberos entries in localize.py
- Corrected cosmetic issues in results feedback in some rules
- Fixed issue where saved user comments were not showing in the GUI
- Fixed issue where user comments were not saved unless the CI had been changed from the default
- Corrected an issue in the ConsoleRootOnly rule that affected OpenSuSE
- Fixed issue where user comments with embedded newlines cause the program to crash
- Implemented GUI help framework and a start to GUI help text
- Corrected issues with output returns from CommandHelper

* Tue Dec 1 2015 David Kennel <dkennel@lanl.gov> - 0.9.2
- ConfigureMacPolicy updated to work around broken behavior in Debian 8's implementation of AppArmor
- Updated FileHelper object adding return value to fixFile and removing unused imports
- Logic bug where SecureIPv6 created files during report mode corrected
- SecureMDNS undo failures corrected
- SystemAccounting undo failure corrected
- Fixed ConfigureKerberos undo issues
- Undo method of rule.py updated to handle removal of directories
- Undo issues in ScheduleStonix corrected
- XinetdAccessControl undo problems corrected
- Fixed issues in the undo of ConsoleRootOnly
- Corrected undo issues with InstallBanners
- Fixed traceback in DisableWeakAuthentication
- Improved user feedback in SecureATCRON

* Tue Oct 27 2015 David Kennel <dkennel@lanl.gov> - 0.9.1
- Corrected traceback in MuteMic rule when run in user context
- Corrected PAM stack on RHEL 7 so that Sudo works with Kerberos
- Updated apt-get install command sytax in aptGet module of package helper
- Multiple fixes to unit tests and test infrastructure
- Corrected traceback in RootMailAlias
- Corrected traceback in ConfigureSudo
- Improved feedback in VerifyAccPerms rule
- Corrected permissions flapping in ConfigureLogging
- Corrected traceback in EnableKernelAuditing
- Corrected traceback in SecureCups
- Updated applicability filters for EnableSELinux rule

* Wed Sep 30 2015 David Kennel <dkennel@lanl.gov> - 0.9.0
- Updated isApplicable() to filter on whether rules should or should not run under the root users context
- Fix to bug in the interaction of installBAnners and SecureSSH that was causing oversized sshd_conf files
- New Rule BootSecurity, mutes the microphone, turns off wireless and turns off bluetooth at every system boot
- Fix subtle bug in ruleKVEditor that caused false positives
- New Rule SecureLDAP checks security on the LDAP server
- Improved feedback in multiple rules
- SecureApacheWebserver now correctly handles RHEL 7 style module layouts
- New Rule EnableKernelAuditing configures auditd according to guidance
- Fixed bug that caused the 'About Stonix' window to be unclosable on gnome 3

* Mon Aug 31 2015 David Kennel <dkennel@lanl.gov> - 0.8.20
- New rule: Remove SUID Games
- New rule: Disable Admin Login Override
- New rule: Disable Login Prompts on Serial Ports
- New rule: Installed Software Verification
- New rule: Xinetd access control
- Fixed multiple issues with Install Banners
- Added wifi to list of allowed names for ConfigureNetworks network locations
- Corrected man page permissions on .deb versions
- Added error handling to Configure Dot Files to suppress errors in edge conditions
- Corrected permissions on /etc/profile.d/tmout.sh for ShellTimeout

* Thu Jul 30 2015 Eric Ball <eball@lanl.gov> - 0.8.19
- New rule: Disable GUI Logon
- New rule: Restrict Mounting
- New rule: Time-out for Login Shells
- New rule: Secure Squid Proxy
- New rule: No Cached FDE Keys
- Added framework unit testing to stonixtest.py
- Unit test added for DisableFTP
- Unit test added for SecureDHCP
- Added undo functionality for DisableCamera
- Fixed issue that caused tracebacks in ConfigureNetworks
- Fixed issue that caused tracebacks in ConfigurePowerManagement
- Improved reliability of ConfigureAIDE
- Heavily refactored InstallBanners
- Improved feedback for ConfigureSystemAuthentication non-compliance


* Tue Jun 30 2015 David Kennel <dkennel@lanl.gov> - 0.8.18
- New rule: Secure the ISC DHCP server
- Fixed an issue that caused tracebacks in SecureMDNS
- Fixed an issue that would cause STONIX to quit if mail relay was not available when a traceback occured
- Fixed unit test issues in the zzzTestFrameworkconfiguration and zzzTestFrameworkServiceHelper
- Corrected traceback in ConfigureLogging
- Unit test added for DisableThumbnailers

* Fri May 29 2015 David Kennel <dkennel@lanl.gov> - 0.8.17
- Fixed multiple issues with SetSSCorners
- Observed behavior on CentOS where DisableThumbnailers is non-compliant after fix
  due to issues with gconf/dbus.
- Fixed bug in MinimizeServices caused by missing commas in a Python list that affected
  non-systemd Linux distributions.

* Thu Apr 30 2015 David Kennel <dkennel@lanl.gov> - 0.8.16
- Major refactor of the isApplicable method and workflow
- Corrected bug in the behavior of RootMailAlias
- SoftwarePatching rule now checks rpmrc files for the nosignature option
- Optional rule to enable system accounting via sysstat and sar
- Refactor of KVADefault for clarity

* Mon Mar 30 2015 David Kennel <dkennel@lanl.gov> - 0.8.15
- Short circut logic added to FilePermissions, report capped at 30,000 bad files
- Corrected bug on OpenSUSE where SHsystemctl was using wrong path
- Guidance update for SecureMTA; postfix now configuring a relayhost

* Mon Mar 2 2015 David Kennel <dkennel@lanl.gov> - 0.8.14

* Thu Jan 29 2015 David Kennel <dkennel@lanl.gov> - 0.8.13
- Corrected logic errors in SecureMDNS
- Eliminated errant email from DisableScreenSavers
- Add unix man page for stonix
- Corrected cosmetic issue with SetNTP
- Fixed NCAF in ConfigureLoggin on OpenSuSE
- Corrected issue in the Service Helper for systemd services
- Corrected cosmetic issue in DisableIPV6

* Tue Jan 6 2015 David Kennel <dkennel@lanl.gov> - 0.8.12
- Fixed permissions on stonix.conf that prevented use of user mode
- Fixed dependency issues on /bin/env in OpenSUSE
- Corrected traceback issues in isApplicable on Fedora
- Fixed stalling in SecureMDNS on RHEL 7
- Fixed discoveros failure in CentOS
- Corrected missing try/catch for cases where PyQT is not available
- BootloaderPerms updated for RHEL 7/CentOS 7
- Stop run button and toolbar added to STONIX GUI

* Mon Dec 1 2014 David Kennel <dkennel@lanl.gov> - 0.8.11

* Mon Nov 3 2014 David Kennel <dkennel@lanl.gov> - 0.8.10
- Fixed ConsoleRootOnly rule on RHEL 7
- Fixed DisableIPV6 rule on RHEL 7
- Fixed EnableSELinux rule on RHEL 7
- Fixed ConfigureLogging rule on Fedora

* Wed Oct 1 2014 David Kennel <dkennel@lanl.gov> - 0.8.9
- Resolved issue in InstallVlock rule
- Added metrics to STONIX execution
- Resolved GUI timing glitches
- Resolved issue where the DisableBluetooth rule killed the GUI on RHEL 7
- Known issue with OpenSUSE 13.1 and minimize services due to a bug in OpenSUSE where some services do not actually turn off via the chkconfig command.
- Resolved non-compliant after fix issues in SetFSMountOptions
- Clarified non-compliance messages in InstallBanners
- DisableUSBStorage refactored and renamed to DisableRemovableStorage
- DOEWARNINGBANNER variable renamed.
- New rule added: Enable Stack Protection
- Resolved issue where the Zypper package helper component did not handle permission denied on repo access correctly.

* Thu Aug 28 2014 David Kennel <dkennel@lanl.gov> - 0.8.8

* Tue Jul 29 2014 David Kennel <dkennel@lanl.gov> - 0.8.7

* Fri Jun 27 2014 David Kennel <dkennel@lanl.gov> - 0.8.6
- 7th Alpha release
- Fixed issue with CIs not showing up in OS X
- Fixed LoginWindow configuration on OS X
- Fixed non-compliant after fix issue in ConfigureSudo
- Fixed Admin SSH restriction in OS X
- Resolved multiple issues in ConfigureLoggin rule
- Fixed unable to restart sysctl messages
- Resolved non-compliant after fix with SecureMTA rule
- Fixed bug that could result in multiple copies of the same rule running
- FilePermissions now has a blacklist feature to ignore file systems
- Fixed non-compliant after fix in TCPWrappers rule
- Fixed traceback in SecureSNMP on OS X
- Fixed non-compliant after fix in SecureCUPS rule
- Fixed SymlinkDangerFiles on OS X
- Fixed non-compliant after fix in EnableSELinux on Ubuntu
- Fixed non-compliant after fix in InstallVLock on Ubuntu
- Fixed non-compliant after fix in SSHTimeout
- Fixed traceback in SSHTimeout
- Fixed SecureHomeDir showing error but reporting compliant
- Fixed multiple bugs in SecureSU
- FilePermissions rule will now remove world write permissions in roots path
- OS Version information now submitted in STONIX error messages
- Fixed traceback in DisableUnusedFS rule
- Fixed traceback in ConfigureKerberos on Debian

* Mon Jun 02 2014 David Kennel <dkennel@lanl.gov> - 0.8.5
- 6th Alpha release
- ConfigureAIDE should now initialize the Database
- SecureATCRON traceback on CentOS fixed
- SetDaemonUmask Traceback on CentOS fixed
- Install Puppet traceback fixed
- ReqAuthSingleUserMode fixed
- RootMailAlias multiple bugs fixed
- SecureHomeDir refactored to elminate bugs
- Fixed cosmetic issue with missing newline at the end of the warning banner
- ScheduleStonix now reports compliant on first fix
- StateChgLogger component now supports logging/recovery of deleted files
- EnableSELinux rule now allows permissive/enforcing mode selection

* Mon Apr 28 2014 David Kennel <dkennel@lanl.gov> - 0.8.4
- Bumped version for 5th alpha.
- Numerous changes:
- Fixed traceback in InstallVlock
- Allowed shorter than 15 min lockouts for screensavers
- Fixed non-compliant after fix bug in screen locking
- Fixed insecure command useage in configure system authentication
- Fixed traceback in DisableIPv6
- Fixed fix mode failure in PasswordExpiration
- Fixed non-compliant after fix bug in PreventXListen
- Fixed multiple bugs in SecureMTA
- Fixed non-compliant after fix bug in SecureSSH
- Fixed traceback in SoftwarePatching on CentOS
- Fixed blocking behavior in GUI. UI now updates while executing.
- Changed CI implementation and invocation in all rules.
- Fixed DisableInteractiveStartup traceback on CentOS.
- Fixed ScheduleStonix traceback on CentOS.
- Fixed DisableScreenSavers non-compliant after fix bug.
- Fixed bug in SetDefaultUserUmask where CI was not referenced in Fix
- Fixed bug in SetFSMountOptions where CI was not referenced in Fix
- Fixed bug in SetNTP where CI was not referenced in Fix
- Fixed bug in setRootDefaults where CI was not referenced in Fix
- Fixed bug in SetupLogwatch where CI was not referenced in Fix
- Fixed bug in TCPWrappers where CI was not referenced in Fix
- Fixed bug in VerifyAccPerms where CI was not referenced in Fix
- Fixed bug in BootloaderPerms where CI was not referenced in Fix
- Fixed bug in InstallBanners where CI was not referenced in Fix
- Fixed bug in ConfigureAIDE where CI was not referenced in Fix
- Fixed bug in DisableUSBStorage where CI was not referenced in Fix
- Fixed bug in CommandHelper that resulted in attribute errors in certain cases.
- Fixed multiple bugs in SecureMDNS.

* Mon Mar 24 2014 David Kennel <dkennel@lanl.gov> - 0.8.3
- Initial release in RPM format.

