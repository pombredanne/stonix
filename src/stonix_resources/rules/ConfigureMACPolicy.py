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
'''
Created on Jan 30, 2013

The ConfigureMACPolicy class enables and configures SELinux on support OS platforms.

@author: bemalmbe
@change: dwalker 3/10/2014
@change: dkennel 04/18/2014 Replaced old style CI invocation
@change: 2015/04/15 dkennel updated for new isApplicable
@change: 2015/10/07 eball Help text cleanup
@change: dwalker 10/20/2015 Update report and fix methods for applicability
@change: Breen Malmberg - 10/26/2015 - merged apparmor code with selinux code; added method doc strings
'''

from __future__ import absolute_import
import traceback
import re
import os
from ..rule import Rule
from ..stonixutilityfunctions import checkPerms, setPerms, readFile, writeFile
from ..stonixutilityfunctions import iterate, resetsecon
from ..logdispatcher import LogPriority
from ..pkghelper import Pkghelper
from ..CommandHelper import CommandHelper


class ConfigureMACPolicy(Rule):
    '''
    The ConfigureMACPolicy class configures either selinux or apparmor
    depending on the os platform.
    @change: dwalker - created two config items, one for enable/disable, and
        another for whether the user wants to use permissive or enforcing
    '''

    def __init__(self, config, environ, logger, statechglogger):
        Rule.__init__(self, config, environ, logger, statechglogger)
        self.logger = logger
        self.rulenumber = 107
        self.rulename = 'ConfigureMACPolicy'
        self.formatDetailedResults("initialize")
        self.mandatory = True
        self.helptext = '''The ConfigureMACPolicy rule configures either \
selinux or apparmor, based on the os platform.  on supported platforms.  \
These programs are called Mandatory Access Control programs and are essential \
for enforcing what certain programs are allowed and not allowed to do.'''
        self.guidance = ['NSA(2.1.1.6)(2.4.2)', 'CCE-3977-6', 'CCE-3999-0',
                         'CCE-3624-4', 'CIS 1.7']
        self.setype = "targeted"
        self.universal = "#The following lines were added by stonix\n"
        self.iditerator = 0
        self.seinstall = False
        self.kernel = True
        self.applicable = {'type': 'white',
                           'family': ['linux']}

        datatype = "bool"
        key = "CONFIGUREMAC"
        instructions = "To prevent the configuration of a mandatory " + \
            "access control policy set the value of CONFIGUREMAC to " + \
            "False. Note: The 'mandatory access control' is either SELinux or AppArmor, depending on your system type."
        default = True
        self.ConfigureMAC = self.initCi(datatype, key, instructions, default)

        datatype2 = "string"
        key2 = "MODE"
        default2 = "permissive"
        instructions2 = "Valid modes for SELinux are: permissive or enforcing. Valid modes for AppArmor are: complain or enforce"
        self.modeci = self.initCi(datatype2, key2, instructions2, default2)

        self.statuscfglist = ['SELinux status:(\s)+enabled',
                              'Current mode:(\s)+(permissive|enforcing)',
                              'Mode from config file:(\s)+(permissive|enforcing)',
                              'Policy from config file:(\s)+(targeted|default)|Loaded policy name:(\s)+(targeted|default)']
        self.localization()

    def localization(self):
        '''
        wrapper for setting up initial variables and helper objects based on which OS type you have

        @return: void
        @author: Breen Malmberg
        '''

        self.initobjs()
        self.setcommon()

        if self.pkghelper.manager == "zypper":
            self.setopensuse()
        if self.pkghelper.manager == "apt-get":
            self.setubuntu()

    def setcommon(self):
        '''
        set common variables for use with both/either ubuntu and/or opensuse

        @return: void
        @author: Breen Malmberg
        '''

        self.ubuntu = False
        self.opensuse = False
        self.detailedresults = ""

        # for generating a new profile, you need the command, plus the target profile name
        self.genprofcmd = '/usr/sbin/aa-genprof'
        self.aaprofiledir = '/etc/apparmor.d/'
        self.aastatuscmd = '/usr/sbin/apparmor_status'
        self.aaunconf = '/usr/sbin/aa-unconfined'

        self.initobjs()

    def initobjs(self):
        '''
        initialize helper objects

        @return: void
        @author: Breen Malmberg
        '''

        try:

            self.cmdhelper = CommandHelper(self.logger)
            self.pkghelper = Pkghelper(self.logger, self.environ)

        except Exception:
            raise

    def setopensuse(self):
        '''
        set variables for opensuse systems

        @return: void
        @author: Breen Malmberg
        '''

        self.opensuse = True
        self.pkgdict = {'libapparmor1': True,
                        'apparmor-profiles': True,
                        'apparmor-utils': True,
                        'apparmor-parser': True,
                        'yast2-apparmor': True,
                        'apparmor-docs': True}
        self.aastartcmd = 'rcapparmor start'
        self.aareloadprofscmd = 'rcapparmor reload'
        self.aastatuscmd = 'rcapparmor status'

    def setubuntu(self):
        '''
        set variables for ubuntu systems

        @return: void
        @author: Breen Malmberg
        '''

        self.ubuntu = True
        self.pkgdict = {'apparmor': True,
                        'apparmor-utils': True,
                        'apparmor-profiles': True}

        self.aastartcmd = 'invoke-rc.d apparmor start'
        self.aaupdatecmd = 'update-rc.d apparmor start 5 S .'
        self.aareloadprofscmd = 'invoke-rc.d apparmor reload'
        self.aadefscmd = 'update-rc.d apparmor defaults'
        self.aastatuscmd = '/usr/sbin/aa-status'

    def report(self):
        '''
        decide which report method(s) to run, based on package manager

        @return: self.compliant
        @rtype: bool
        @author: Derek Walker
        @change: Breen Malmberg - 10/26/2015 - filled in stub method; added method doc string
        '''

        self.compliant = True
        self.detailedresults = ''

        try:
            if self.pkghelper.manager in ("yum", "portage"):
                if not self.reportSELinux():
                    self.compliant = False
            elif self.pkghelper.manager in ("zypper", "apt-get"):
                if not self.reportAppArmor():
                    self.compliant = False
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("report", self.compliant, self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return self.compliant

    def reportAppArmor(self):
        '''
        run report actions for each piece of apparmor in sequence

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True

        try:

            if not self.reportAApkg():
                retval = False
            if retval:
                if not self.reportAAstatus():
                    retval = False
                if not self.reportAAprofs():
                    retval = False

            if self.needsrestart:
                self.detailedresults += '\nSystem needs to be restarted before apparmor module can be loaded.'

        except Exception:
            raise
        return retval

    def reportAApkg(self):
        '''
        check whether the apparmor package is installed

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        # defaults
        retval = True
        self.needsrestart = False
        for pkg in self.pkgdict:
            self.pkgdict[pkg] = True

        try:

            if not self.pkgdict:
                self.logger.log(LogPriority.DEBUG, "The list of packages needed is blank")

            for pkg in self.pkgdict:
                if not self.pkghelper.check(pkg):
                    self.pkgdict[pkg] = False
            for pkg in self.pkgdict:
                if not self.pkgdict[pkg]:
                    retval = False
                    self.detailedresults += '\nPackage: ' + str(pkg) + ' is not installed'
                    self.needsrestart = True

        except Exception:
            raise
        return retval

    def reportAAstatus(self):
        '''
        check whether the apparmor module is loaded

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True

        try:

            # we cannot use the apparmor utilities to check the status, if they are not installed!
            if not self.pkgdict['apparmor-utils']:
                self.detailedresults += '\nCannot check apparmor status without apparmor-utils installed'
                retval = False
                return retval

            self.cmdhelper.executeCommand(self.aastatuscmd)
            output = self.cmdhelper.getOutputString()
            errout = self.cmdhelper.getErrorString()
            if re.search('AppArmor not enabled', output):
                self.needsrestart = True
                retval = False
            if re.search('error|Traceback', errout):
                retval = False
                self.detailedresults += '\nThere was an error while attempting to run command: ' + str(self.aastatuscmd)
                self.detailedresults += '\nThe error was: ' + str(errout)
                self.logger.log(LogPriority.DEBUG, self.detailedresults)
            if not re.search('apparmor module is loaded', output):
                retval = False
                self.detailedresults += '\napparmor module is not loaded'

        except Exception:
            raise
        return retval

    def reportAAprofs(self):
        '''
        check whether or not there are any unconfined (by apparmor) services or applications

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        self.unconflist = []
        unconfined = False
        retval = True

        try:

            if not self.pkgdict['apparmor-utils']:
                self.detailedresults += '\nCannot check apparmor profile status without apparmor-utils installed'
                retval = False
                return retval
            if not self.pkgdict['apparmor-profiles']:
                self.detailedresults += '\nCannot accurately determine profile status without apparmor-profiles installed'
                retval = False
                return retval

            self.cmdhelper.executeCommand(self.aaunconf)
            errout = self.cmdhelper.getErrorString()
            output = self.cmdhelper.getOutputString()
            if re.search('error|Traceback', output):
                retval = False
                if re.search('codecs\.py', output):
                    self.detailedresults += '\nThere is a bug with running a required command in this version of Debian. \
                    This rule will remain NCAF until Debian can fix this issue. This is not a STONIX bug.'
            if re.search('error|Traceback', errout):
                retval = False
                if re.search('codecs\.py', errout):
                    self.detailedresults += '\nThere is a bug with running a required command in this version of Debian. \
                    This rule will remain NCAF until Debian can fix this issue. This is not a STONIX bug.'
                else:
                    self.detailedresults += '\nThere was an error running command: ' + str(self.aaunconf)
                    self.detailedresults += '\nThe error was: ' + str(errout)
                    self.logger.log(LogPriority.DEBUG, "Error running command: " + str(self.aaunconf) + "\nError was: " + str(errout))
            output = self.cmdhelper.getOutput()
            for line in output:
                if re.search('not confined', line):
                    retval = False
                    unconfined = True
                    sline = line.split()
                    self.unconflist.append(str(sline[1]))
                    self.detailedresults += '\n' + str(sline[1]) + ' is not confined by apparmor'
            if unconfined:
                self.detailedresults += "\n\nIf you have services or applications which are unconfined by apparmor, this can only be corrected manually, by the administrator of your system. (See the man page for apparmor)."

        except Exception:
            raise
        return retval

    def reportSELinux(self):
        '''
        determine whether SELinux is already enabled and properly configured.
        self.compliant, self.detailed results and self.currstate properties are
        updated to reflect the system status. self.rulesuccess will be updated
        if the rule does not succeed.

        @return bool
        @author bemalmbe
        @change: dwalker 4/04/2014 implemented commandhelper, added more
            accurate implementation per system basis for apt-get systems
            especially.
        '''
        self.detailedresults = ""
        self.mode = self.modeci.getcurrvalue()
        self.ch = CommandHelper(self.logger)
        compliant = True
        # the selinux path is the same for all systems
        self.path1 = "/etc/selinux/config"
        self.tpath1 = "/etc/selinux/config.tmp"
        # set the appropriate name of the selinux package
        if self.pkghelper.manager == "apt-get":
            if re.search("Debian", self.environ.getostype()):
                self.selinux = "selinux-basics"
            else:
                self.selinux = "selinux"
        elif self.pkghelper.manager == "yum":
            self.selinux = "libselinux"
        # set the grub path for each system and certain values to be found
        # inside the file
        if re.search("Red Hat", self.environ.getostype()) or \
                re.search("Fedora", self.environ.getostype()):
            if re.search("^7", str(self.environ.getosver()).strip()) or \
                    re.search("^20", str(self.environ.getosver()).strip()):
                self.setype = "targeted"
                self.path2 = "/etc/default/grub"
                self.tpath2 = "/etc/default/grub.tmp"
                self.perms2 = [0, 0, 420]
            else:
                self.setype = "targeted"
                self.path2 = "/etc/grub.conf"
                self.tpath2 = "/etc/grub.conf.tmp"
                self.perms2 = [0, 0, 384]
        elif self.pkghelper.manager == "apt-get" or self.pkghelper.manager == "zypper":
            self.setype = "default"
            self.path2 = "/etc/default/grub"
            self.tpath2 = "/etc/default/grub.tmp"
            self.perms2 = [0, 0, 420]
        else:
            self.setype = "targeted"
            self.path2 = "/etc/grub.conf"
            self.tpath2 = "/etc/grub.conf.tmp"
            self.perms2 = [0, 0, 384]

        if not self.pkghelper.check(self.selinux):
            compliant = False
            self.detailedresults += "selinux is not even installed\n"
            self.formatDetailedResults("report", self.compliant,
                                       self.detailedresults)
            self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        else:
            self.f1 = readFile(self.path1, self.logger)
            self.f2 = readFile(self.path2, self.logger)
            if self.f1:
                if not checkPerms(self.path1, [0, 0, 420], self.logger):
                    compliant = False
                conf1 = True
                conf2 = True
                found1 = False
                found2 = False
                for line in self.f1:
                    if re.match("^#", line) or re.match("^\s*$", line):
                        continue
                    if re.match("^SELINUX\s{0,1}=", line.strip()):
                        found1 = True
                        if re.search("=", line.strip()):
                            temp = line.split("=")
                            if temp[1].strip() == self.mode or \
                                    temp[1].strip() == "enforcing":
                                continue
                            else:
                                conf1 = False
                    if re.match("^SELINUXTYPE", line.strip()):
                        found2 = True
                        if re.search("=", line.strip()):
                            temp = line.split("=")
                            if temp[1].strip() == self.setype:
                                continue
                            else:
                                conf2 = False
                if not found1 or not found2:
                    self.detailedresults += "The desired contents " + \
                        "were not found in /etc/selinux/config\n"
                    compliant = False
                elif not conf1 or not conf2:
                    self.detailedresults += "The desired contents " + \
                        "were not found in /etc/selinux/config\n"
                    compliant = False
            else:
                self.detailedresults += "/etc/selinux/config file " + \
                    "is blank\n"
                compliant = False
            if self.f2:
                conf1 = False
                conf2 = False
                if self.pkghelper.manager == "apt-get":
                    if not checkPerms(self.path2, self.perms2,
                                      self.logger):
                        compliant = False
                    for line in self.f2:
                        if re.match("^#", line) or re.match("^\s*$",
                                                            line):
                            continue
                        if re.match("^GRUB_CMDLINE_LINUX_DEFAULT",
                                    line.strip()):
                            if re.search("=", line):
                                temp = line.split("=")
                                if re.search("security=selinux",
                                             temp[1].strip()):
                                    conf1 = True
                                if re.search("selinux=0",
                                             temp[1].strip()):
                                    conf2 = True
                    if conf1 or conf2:
                        self.detailedresults += "Grub file is non compliant\n"
                        compliant = False
                else:
                    conf1 = False
                    conf2 = False
                    for line in self.f2:
                        if re.match("^#", line) or re.match("^\s*$",
                                                            line):
                            continue
                        if re.match("^kernel", line.strip()):
                            if re.search("^selinux=0", line.strip()):
                                conf1 = True
                            if re.match("^enforcing=0", line.strip()):
                                conf2 = True
                    if conf1 or conf2:
                        self.detailedresults += "Grub file is non compliant\n"
                        compliant = False
            if self.ch.executeCommand(["/usr/sbin/sestatus"]):
                output = self.ch.getOutput()
                error = self.ch.getError()
                if output:
                    # self.statuscfglist is a list of regular expressions to match
                    for item in self.statuscfglist:
                        found = False
                        for item2 in output:
                            if re.search(item, item2):
                                found = True
                                break
                        if not found:
                            if self.pkghelper.manager == "apt-get":
                                if self.seinstall:
                                    self.detailedresults += "Since stonix \
just installed selinux, you will need to reboot your system before this rule \
shows compliant.  After stonix is finished running, reboot system, run stonix \
and do a report run on EnableSELinux rule again to verify if fix was \
completed successfully\n"
                            else:
                                self.detailedresults += "contents of \
sestatus output is not what it's supposed to be\n"
                                compliant = False
                elif error:
                    self.detailedresults += "There was an error running \
the sestatus command to see if selinux is configured properly\n"
                    compliant = False
        return compliant

###############################################################################
    def fix(self):
        '''
        decide which fix method(s) to run, based on package manager

        @return: fixresult
        @rtype: bool
        @author: Derek Walker
        @change: Breen Malmberg - 10/26/2015 - filled in stub method; added doc string; 
                                                changed method to use correct return variable
        '''

        fixresult = True
        self.detailedresults = ''
        self.iditerator = 0

        try:

            if self.ConfigureMAC.getcurrvalue():

                if self.pkghelper.manager in ("yum", "portage"):
                    if not self.fixSELinux():
                        fixresult = False
                elif self.pkghelper.manager in ("zypper", "apt-get"):
                    if not self.fixAppArmor():
                        fixresult = False
                else:
                    self.detailedresults += '\nCould not identify your OS type, or OS not supported for this rule.'

            else:
                self.detailedresults += '\nThe CI for this rule was not enabled. Nothing was done.'
                self.logger.log(LogPriority.DEBUG, self.detailedresults)

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", fixresult, self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return fixresult

    def fixAppArmor(self):
        '''
        wrapper to decide which fix actions to run and in what order, for apparmor

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True

        try:

            if self.modeci.getcurrvalue() in ['complain', 'permissive']:
                aamode = '/usr/sbin/aa-complain'
            elif self.modeci.getcurrvalue() == ['enforce', 'enforcing']:
                aamode = '/usr/sbin/aa-enforce'
            if not aamode:
                self.detailedresults += '\nNo valid mode was specified for apparmor profiles. Valid modes include: enforce, or complain.'
                self.detailedresults += '\nFix was not run to completion. Please enter a valid mode and try again.'
                self.logger.log(LogPriority.DEBUG, self.detailedresults)
                retval = False
                return retval

            self.aaprofcmd = aamode + ' ' + self.aaprofiledir + '*'

            if not self.fixAApkg():
                retval = False
            if retval: # should not continue unless apparmor package is installed
                if not self.fixAAstatus():
                    retval = False

        except Exception:
            raise
        return retval

    def fixAApkg(self):
        '''
        install all packages which are required for apparmor to function properly

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True

        try:

            for pkg in self.pkgdict:
                if not self.pkgdict[pkg]:
                    if not self.pkghelper.install(pkg):
                        retval = False
                        self.detailedresults += '\nFailed to install package: ' + str(pkg)

        except Exception:
            raise
        return retval

    def fixAAstatus(self):
        '''
        ensure that apparmor is configured correctly and running

        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True
        editedgrub = False
        apparmorfound = False

        try:

            if self.ubuntu:

                self.logger.log(LogPriority.DEBUG, "Detected that this is an apt-get based system. Looking for grub configuration file...")

                if os.path.exists('/etc/default/grub'):

                    grubpath = '/etc/default/grub'
                    tmpgrubpath = grubpath + '.stonixtmp'
                    self.logger.log(LogPriority.DEBUG, "Grub configuration file found at: " + str(grubpath))

                    self.logger.log(LogPriority.DEBUG, "Reading grub configuration file...")
                    fr = open(grubpath, 'r')
                    contentlines = fr.readlines()
                    fr.close()

                    self.logger.log(LogPriority.DEBUG, "Got grub configuration file contents. Looking for required apparmor kernel config line...")

                    for line in contentlines:
                        if re.search('GRUB_CMDLINE_LINUX="', line):
                            if not re.search('apparmor=1 security=apparmor', line):
                                self.logger.log(LogPriority.DEBUG, "Required apparmor kernel line not found. Adding it...")
                                contentlines = [c.replace(line, line[:-2] + ' apparmor=1 security=apparmor"\n') for c in contentlines]
                                editedgrub = True
                            else:
                                apparmorfound = True
                    if not editedgrub and not apparmorfound:
                        contentlines.append('\nGRUB_CMDLINE_LINUX="apparmor=1 security=apparmor"\n')
                        editedgrub = True

                    if editedgrub:
                        self.logger.log(LogPriority.DEBUG, "Added apparmor kernel config line to contents. Writing contents to grub config file...")
                        tfw = open(tmpgrubpath, 'w')
                        tfw.writelines(contentlines)
                        tfw.close()

                        self.iditerator += 1
                        myid = iterate(self.iditerator, self.rulenumber)
                        event = {'eventtype': 'conf',
                                 'filepath': grubpath}
                        self.statechglogger.recordchgevent(myid, event)
                        self.statechglogger.recordfilechange(tmpgrubpath, grubpath, myid)

                        os.rename(tmpgrubpath, grubpath)
                        os.chmod(grubpath, 0644)
                        os.chown(grubpath, 0, 0)
                        self.logger.log(LogPriority.DEBUG, "Finished writing apparmor kernel config line to grub config file")
                        self.needsrestart = True

                        updategrub = 'update-grub'

                        self.logger.log(LogPriority.DEBUG, "Running update-grub command to update grub kernel boot configuration...")
                        self.cmdhelper.executeCommand(updategrub)
                        errout = self.cmdhelper.getErrorString()
                        if re.search('error|Traceback', errout):
                            retval = False
                            self.detailedresults += '\nError updating grub configuration: ' + str(errout)
                            self.logger.log(LogPriority.DEBUG, "Error executing " + str(updategrub) + "\nError was: " + str(errout))
                            return retval
                        self.logger.log(LogPriority.DEBUG, "Finished successfully updating grub kernel boot configuration...")

                else:
                    self.logger.log(LogPriority.DEBUG, "Unable to locate grub configuration file")

                self.logger.log(LogPriority.DEBUG, "Checking if the system needs to be restarted first in order to continue...")

                if not self.needsrestart:

                    self.logger.log(LogPriority.DEBUG, "System does not require restart to continue configuring apparmor. Proceeding...")

                    self.cmdhelper.executeCommand(self.aadefscmd)
                    errout = self.cmdhelper.getErrorString()
                    if re.search('error|Traceback', errout):
                        retval = False
                        self.detailedresults += '\nThere was an error running command: ' + str(self.aadefscmd)
                        self.detailedresults += '\nThe error was: ' + str(errout)

                    self.cmdhelper.executeCommand(self.aaprofcmd)
                    errout = self.cmdhelper.getErrorString()
                    if re.search('error|Traceback', errout):
                        retval = False
                        self.detailedresults += '\nThere was an error running command: ' + str(self.aaprofcmd)
                        self.detailedresults += '\nThe error was: ' + str(errout)

                    self.cmdhelper.executeCommand(self.aareloadprofscmd)
                    errout = self.cmdhelper.getErrorString()
                    if re.search('error|Traceback', errout):
                        retval = False
                        self.detailedresults += '\nThere was an error running command: ' + str(self.aareloadprofscmd)
                        self.detailedresults += '\nThe error was: ' + str(errout)

                    self.cmdhelper.executeCommand(self.aaupdatecmd)
                    errout = self.cmdhelper.getErrorString()
                    if re.search('error|Traceback', errout):
                        retval = False
                        self.detailedresults += '\nThere was an error running command: ' + str(self.aaupdatecmd)
                        self.detailedresults += '\nThe error was: ' + str(errout)

                        self.cmdhelper.executeCommand(self.aastartcmd)
                        errout2 = self.cmdhelper.getErrorString()
                        if re.search('error|Traceback', errout2):
                            retval = False
                            self.detailedresults += '\nThere was an error running command: ' + str(self.aastartcmd)
                            self.detailedresults += '\nThe error was: ' + str(errout2)

                else:
                    self.logger.log(LogPriority.DEBUG, "System requires a restart before continuing to configure apparmor. Will NOT restart automatically.")
                    self.detailedresults += '\nApparmor was just installed and/or added to the kernel boot config. You will need to restart your system and run this rule in fix again before it can configure properly.'
                    retval = False
                    return retval

            elif self.opensuse:

                self.cmdhelper.executeCommand(self.aaprofcmd)
                errout = self.cmdhelper.getErrorString()
                if re.search('error|Traceback', errout):
                    retval = False
                    self.detailedresults += '\nThere was an error running command: ' + str(self.aaprofcmd)
                    self.detailedresults += '\nThe error was: ' + str(errout)

                self.cmdhelper.executeCommand(self.aareloadprofscmd)
                errout = self.cmdhelper.getErrorString()
                if re.search('error|Traceback', errout):
                    retval = False
                    self.detailedresults += '\nThere was an error running command: ' + str(self.aareloadprofscmd)
                    self.detailedresults += '\nThe error was: ' + str(errout)

                self.cmdhelper.executeCommand(self.aastartcmd)
                errout = self.cmdhelper.getErrorString()
                if re.search('error|Traceback', errout):
                    retval = False
                    self.detailedresults += '\nThere was an error running command: ' + str(self.aastartcmd)
                    self.detailedresults += '\nThe error was: ' + str(errout)
            else:
                self.detailedresults += "\nCould not identify your OS type, or OS not supported"
                retval = False
                return retval
        except Exception:
            raise
        return retval

    def fixSELinux(self):
        '''
        enable and configure selinux. self.rulesuccess will be updated if this
        method does not succeed.

        @author bemalmbe
        @change: dwalker 4/04/2014 implemented commandhelper, added more
            accurate implementation per system basis for apt-get systems
            especially.
        '''
        if not self.ConfigureMAC.getcurrvalue():
            return
        self.detailedresults = ""
        if not self.kernel:
            return
        #clear out event history so only the latest fix is recorded
        self.iditerator = 0
        eventlist = self.statechglogger.findrulechanges(self.rulenumber)
        for event in eventlist:
            self.statechglogger.deleteentry(event)

        if not self.pkghelper.check(self.selinux):
            if self.pkghelper.checkAvailable(self.selinux):
                if not self.pkghelper.install(self.selinux):
                    self.rulesuccess = False
                    self.detailedresults += "selinux was not able to be \
installed\n"
                    self.formatDetailedResults("report", self.compliant,
                                               self.detailedresults)
                    self.logdispatch.log(LogPriority.INFO, self.detailedresults)
                    return
                else:
                    self.seinstall = True
            else:
                self.detailedresults += "selinux package not available \
for install on this linux distribution\n"
                self.rulesuccess = False
                self.formatDetailedResults("report", self.rulesuccess,
                                           self.detailedresults)
                return
        self.f1 = readFile(self.path1, self.logger)
        self.f2 = readFile(self.path2, self.logger)
        if self.f1:
            if not checkPerms(self.path1, [0, 0, 420], self.logger):
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)
                setPerms(self.path1, [0, 0, 420], self.logger,
                         self.statechglogger, myid)
                self.detailedresults += "Corrected permissions on file: \
" + self.path1 + "\n"
            val1 = ""
            tempstring = ""
            for line in self.f1:
                if re.match("^#", line) or re.match("^\s*$", line):
                    tempstring += line
                    continue
                if re.match("^SELINUX\s{0,1}=", line.strip()):
                    if re.search("=", line.strip()):
                        temp = line.split("=")
                        if temp[1].strip() == "permissive" or temp[1].strip() == "enforcing":
                            val1 = temp[1].strip()
                        if val1 != self.modeci.getcurrvalue():
                            val1 = self.modeci.getcurrvalue()
                            continue
                if re.match("^SELINUXTYPE", line.strip()):
                    continue
                else:
                    tempstring += line
            tempstring += self.universal
            if val1:
                tempstring += "SELINUX=" + val1 + "\n"
            else:
                tempstring += "SELINUX=permissive\n"
            tempstring += "SELINUXTYPE=" + self.setype + "\n"

        else:
            tempstring = ""
            tempstring += self.universal
            tempstring += "SELINUX=permissive\n"
            tempstring += "SELINUXTYPE=" + self.setype + "\n"
        if writeFile(self.tpath1, tempstring, self.logger):
            self.iditerator += 1
            myid = iterate(self.iditerator, self.rulenumber)
            event = {"eventtype": "conf",
                     "filepath": self.path1}
            self.statechglogger.recordchgevent(myid, event)
            self.statechglogger.recordfilechange(self.path1, self.tpath1,
                                                 myid)
            os.rename(self.tpath1, self.path1)
            os.chown(self.path1, 0, 0)
            os.chmod(self.path1, 420)
            resetsecon(self.path1)
            self.detailedresults += "Corrected the contents of the file: \
" + self.path1 + " to be compliant\n"
        else:
            self.rulesuccess = False
        if self.f2:
            if not checkPerms(self.path2, self.perms2, self.logger):
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)
                setPerms(self.path2, self.perms2, self.logger,
                         self.statechglogger, myid)
                self.detailedresults += "Corrected permissions on file: \
" + self.path2 + "\n"
            if self.pkghelper.manager == "apt-get":
                tempstring = ""
                for line in self.f2:
                    if re.match("^GRUB_CMDLINE_LINUX_DEFAULT", line.strip()):
                        newstring = re.sub("security=[a-zA-Z0-9]+", "", line)
                        newstring = re.sub("selinux=[a-zA-Z0-9]+", "", newstring)
                        newstring = re.sub("\s+", " ", newstring)
                        tempstring += newstring + "\n"
                    else:
                        tempstring += line
            else:
                tempstring = ""
                for line in self.f2:
                    if re.match("^kernel", line):
                        temp = line.strip().split()
                        i = 0
                        for item in temp:
                            if re.search("selinux", item):
                                temp.pop(i)
                                i += 1
                                continue
                            if re.search("enforcing", item):
                                temp.pop(i)
                                i += 1
                                continue
                            i += 1
                        tempstringtemp = ""
                        for item in temp:
                            tempstringtemp += item
                        tempstringtemp += "\n"
                        tempstring += tempstringtemp
                    else:
                        tempstring += line
            if tempstring:
                if writeFile(self.tpath2, tempstring, self.logger):
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    event = {"eventtype": "conf",
                             "filepath": self.path2}
                    self.statechglogger.recordchgevent(myid, event)
                    self.statechglogger.recordfilechange(self.path2,
                                                         self.tpath2, myid)
                    os.rename(self.tpath2, self.path2)
                    os.chown(self.path2, self.perms2[0], self.perms2[1])
                    os.chmod(self.path2, self.perms2[2])
                    resetsecon(self.path2)
                    self.detailedresults += "Corrected the contents of \
the file: " + self.path2 + " to be compliant\n"
                else:
                    self.rulesuccess = False
        if not self.seinstall:
            if self.pkghelper.manager == "apt-get":
                if re.search("Debian", self.environ.getostype()):
                    cmd = ["/usr/sbin/selinux-activate"]
                elif re.search("Ubuntu", self.environ.getostype()):
                    cmd = ["/usr/sbin/setenforce", "Enforcing"]
                if self.ch.executeCommand(cmd):
                    if not self.ch.getReturnCode() == 0:
                        self.rulesuccess = False
