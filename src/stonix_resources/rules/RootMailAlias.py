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
Created on Nov 4, 2013

Set an alias for root mail on the system so that it is read by an actual human.

@author: Breen Malmberg
@change: 02/16/2014 ekkehard Implemented self.detailedresults flow
@change: 02/16/2014 ekkehard Implemented isapplicable
@change: 04/21/2014 dkennel Updated CI invocation, fixed bug where boolean CI
was not checked before exectuing fix()
@change: 05/08/2014 dwalker fixing non compliant after fix issues, will be
    refactoring entire rule
@change: 05/28/2014 dwalker refactored rule so that would show compliant after
    fix on mac os x
@change: 2014/10/17 ekkehard OS X Yosemite 10.10 Update
@change: 2015/04/17 dkennel updated for new isApplicable
@change: 2015/04/28 dkennel changed default2 for ci2 to "root@localhost".
    Original had local domain name appended which provides no value.
@change: 2015/08/26 ekkehard [artf37780] : RootMailAlias(251) - NCAF & Lack of detail in Results - OS X El Capitan 10.11
@change: Breen Malmberg, 9/3/2015, re-write of report and fix methods; added helper methods; added/fixed doc strings;
            removed unused imports
@change: eball 2015/09/24 Stopped Pkghelper calls from being made in OS X
'''

from __future__ import absolute_import

from ..rule import Rule
from ..logdispatcher import LogPriority
from ..stonixutilityfunctions import checkPerms
from ..stonixutilityfunctions import iterate, resetsecon
from ..pkghelper import Pkghelper

import os
import re
import traceback


class RootMailAlias(Rule):
    '''
    Set an alias for root mail on the system so that it is read by an actual
    human.
    '''

    def __init__(self, config, environ, logger, statechglogger):
        '''
        Constructor
        '''

        Rule.__init__(self, config, environ, logger, statechglogger)
        self.logger = logger
        self.rulenumber = 251
        self.rulename = 'RootMailAlias'
        self.formatDetailedResults("initialize")
        self.mandatory = True
        self.helptext = 'Set an alias for root mail on the system so that it is read by an actual human.'
        self.guidance = ['none']

        datatype = 'bool'
        key = 'Root Mail Alias'
        instructions = 'To prevent the setting of an alias for root mail, set the value of Root Mail Alias to False.'
        default = True
        self.ci1 = self.initCi(datatype, key, instructions, default)

        datatype2 = 'string'
        key2 = 'Root Alias Address'
        instructions2 = 'Please specify the email address which should receive root mail for this system.'
        default2 = ''
        self.ci2 = self.initCi(datatype2, key2, instructions2, default2)

        self.iditerator = 0
        self.applicable = {'type': 'white',
                           'family': ['linux', 'solaris', 'freebsd'],
                           'os': {'Mac OS X': ['10.9', 'r', '10.11.10']}}

        self.localization()
        self.myos = self.environ.getostype().lower()

###############################################################################

    def localization(self):
        '''
        set up common class variables
        call os-specific variable configuration methods
        '''

        try:

            self.logger.log(LogPriority.DEBUG, "Beginning localization of class variables, based on OS/distribution type...")
            if self.environ.getosfamily() == 'linux':
                self.setlinux()
                self.ph = Pkghelper(self.logger, self.environ)
            elif self.environ.getosfamily() == 'darwin':
                self.setmac()
            self.logger.log(LogPriority.DEBUG, "Setting up common class variables...")
            self.fileperms = [0, 0, 420]
            self.aliasformat = "[^@]+@[^@]+\.[^@]+"
            self.aliasfiletmp = self.aliasfile + '.stonixtmp'

        except Exception:
            raise

    def setlinux(self):
        '''
        set up class variables for use with linux
        '''

        try:

            self.logger.log(LogPriority.DEBUG, "Configuring class variables for Linux systems...")
            self.aliasfile = ''
            aliasfilelocs = ['/etc/mail/aliases', '/etc/aliases']
            aliasfiledefault = '/etc/aliases'
            for loc in aliasfilelocs:
                if os.path.exists(loc):
                    self.aliasfile = loc
            if not self.aliasfile:
                self.aliasfile = aliasfiledefault

        except Exception:
            raise

    def setmac(self):
        '''
        set up class variables for use with mac os x
        '''

        try:

            self.logger.log(LogPriority.DEBUG, "Configuring class variables for Mac OS X systems...")
            self.aliasfile = ''
            aliasfiledefault = '/private/etc/aliases'
            aliasfilelocs = ['/private/etc/aliases', '/private/etc/postfix/aliases']
            for loc in aliasfilelocs:
                if os.path.exists(loc):
                    self.aliasfile = loc
            if not self.aliasfile:
                self.aliasfile = aliasfiledefault

        except Exception:
            raise

    def getFileContents(self, filepath):
        '''
        retrieve file contents of given file path; return them in a list

        @param filepath: string full path to file to read
        @return: contentlines
        @rtype: list
        @author: Breen Malmberg
        '''

        contentlines = []

        self.logger.log(LogPriority.DEBUG, "Retrieving contents of " + str(filepath) + " ...")
        try:

            if not os.path.exists(filepath):
                self.logger.log(LogPriority.DEBUG, "specified filepath did not exist; returning empty set")
                return contentlines

            f = open(filepath, 'r')
            contentlines = f.readlines()
            f.close()

        except Exception:
            raise
        return contentlines

    def checkContents(self, searchterm, contentlines):
        '''
        check the given search parameter for a match in given list

        @param searchterm: string regex to look for a match for
        @param contentlines: list list of strings to check for given search term
        @return: found
        @rtype: bool
        @author: Breen Malmberg
        '''

        found = False

        self.logger.log(LogPriority.DEBUG, "Checking specified file contents for match with search term: " + str(searchterm) + " ...")
        try:

            if not contentlines:
                self.logger.log(LogPriority.DEBUG, "specified contentlines is an empty set; returning False")
                return found

            if not searchterm:
                self.logger.log(LogPriority.DEBUG, "specified searchterm is an empty string; returning False")
                return found

            for line in contentlines:
                if re.search(searchterm, line):
                    found = True

        except Exception:
            raise
        return found

    def report(self):
        '''
        Check the /etc/aliases file for the existence of an alias mail address
        to send root's mail to

        @return: self.compliant
        @rtype: bool
        @author: Breen Malmberg
        @change: dwalker
        @change: Breen Malmberg, 9/3/2015, complete re-write of method
        '''

        self.detailedresults = ""
        self.compliant = True

        if not re.search("os x", self.myos) and self.ph.manager == 'apt-get':
            self.searchstring = '^Postmaster:\s+' + str(self.ci2.getcurrvalue())
            self.fixstring = 'Postmaster: ' + str(self.ci2.getcurrvalue())
            self.partialstring = '^Postmaster:'
        else:
            self.searchstring = '^root:\s+' + str(self.ci2.getcurrvalue())
            self.fixstring = 'root: ' + str(self.ci2.getcurrvalue())
            self.partialstring = '^root:'

        try:

            # check format of user-entered root mail alias address
            self.logger.log(LogPriority.DEBUG, "Checking user-entered value for root mail alias for correct format...")
            if not re.search(self.aliasformat, str(self.ci2.getcurrvalue())):
                self.compliant = False
                self.detailedresults += '\nUser-entered root mail alias is not a valid email address format'

            # check if the alias file has the correct configuration entry
            self.logger.log(LogPriority.DEBUG, "Checking root mail alias file for correct configuration...")
            contentlines = self.getFileContents(self.aliasfile)
            if not self.checkContents(self.searchstring, contentlines):
                self.detailedresults += '\nUnable to find root mail alias address in file: ' + str(self.aliasfile)
                self.compliant = False

            # check if the alias file has the correct permissions
            self.logger.log(LogPriority.DEBUG, "Checking root mail alias file for correct permissions...")
            if not checkPerms(self.aliasfile, self.fileperms, self.logger):
                self.detailedresults += '\nFile ' + str(self.aliasfile) + ' does not have the correct ownership and permissions: ' + ','.join(str(p) for p in self.fileperms)
                self.compliant = False

            # check if system is apt-get based, and if it is, whether or not mailman package is installed
            self.logger.log(LogPriority.DEBUG, "Checking if this is an apt-get based system...")
            if not re.search("os x", self.myos) and self.ph.manager == "apt-get":
                self.logger.log(LogPriority.DEBUG, "This is an apt-get based system. Checking if mailman is installed...")
                if not self.ph.check("mailman"):
                    self.detailedresults += '\nPackage: mailman is not installed'
                    self.compliant = False

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("report", self.compliant,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return self.compliant

###############################################################################

    def fix(self):
        '''
        Add an alias for the root mail on the system to the /etc/aliases file

        @return: fixsuccess
        @rtype: bool
        @author: Breen Malmberg
        @change: dwalker
        @change: Breen Malmberg, 9/3/2015, complete re-write of method
        '''

        fixsuccess = True
        self.detailedresults = ""
        self.iditerator = 0

        try:

            if not self.ci1.getcurrvalue():
                self.logger.log(LogPriority.DEBUG, "Rule was not enabled. Fix did not run.")
                return
            if self.ci2.getcurrvalue():
                if not re.search("[^@]+@[^@]+\.[^@]+", self.ci2.getcurrvalue()):
                    self.logger.log(LogPriority.DEBUG, "User-entered root mail alias address is not in the correct format. Nothing was done.")
                    return

            # fix the file contents
            fixsuccess = self.fixFileContents(self.aliasfile)

            # install mailman, if apt-get based
            if not re.search("os x", self.myos) and self.ph.manager == "apt-get":
                self.ph.install("mailman")

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", fixsuccess,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return fixsuccess

    def fixFileContents(self, filepath):
        '''
        wrapper for the fix actions

        @param filepath: string full path to file to fix
        @return: retval
        @rtype: bool
        @author: Breen Malmberg
        '''

        retval = True

        try:

            if not self.replaceFileContents(filepath):
                retval = self.appendFileContents(filepath)

        except Exception:
            raise
        return retval

    def replaceFileContents(self, filepath):
        '''
        replace any existing configuration of root mail alias

        @param filepath: string full path to the file to edit
        @return: replaced
        @rtype: bool
        @author: Breen Malmberg
        '''

        replaced = False
        tmppath = filepath + '.stonixtmp'

        try:

            if not os.path.exists(filepath):
                self.logger.log(LogPriority.DEBUG, "Specified file path: " + str(filepath) + " does not exist. Will attempt to create it.")
                return replaced

            contentlines = self.getFileContents(filepath)
            for line in contentlines:
                if re.search(self.partialstring, line):
                    contentlines = [c.replace(line, '# Added by STONIX\n' + self.fixstring + '\n') for c in contentlines]
                    replaced = True
            if replaced:
                f = open(tmppath, 'w')
                f.writelines(contentlines)
                f.close
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)
                event = {"eventtype": "conf",
                         "filepath": filepath}
                self.statechglogger.recordchgevent(myid, event)
                self.statechglogger.recordfilechange(filepath, tmppath, myid)
                os.rename(tmppath, filepath)
                os.chown(filepath, 0, 0)
                os.chmod(filepath, 420)
                resetsecon(filepath)
                self.logger.log(LogPriority.DEBUG, "Replaced existing config line with correct one")

        except Exception:
            raise
        return replaced

    def appendFileContents(self, filepath):
        '''
        if the root mail alias configuration line doesn't exist in the file, append it

        @param filepath: string full path to file to edit
        @return: appended
        @rtype: bool
        @author: Breen Malmberg
        '''

        appended = False
        tmppath = filepath + '.stonixtmp'

        try:

            if not os.path.exists(filepath):
                contentlines = ['# Created by STONIX\n', self.fixstring + '\n']

                f = open(filepath, 'w')
                f.writelines(contentlines)
                f.close()
                os.chown(filepath, 0, 0)
                os.chmod(filepath, 420)
                resetsecon(filepath)
                appended = True
            else:
                contentlines = self.getFileContents(filepath)
                contentlines.append('\n# Added by STONIX\n' + self.fixstring + '\n')

                f = open(tmppath, 'w')
                f.writelines(contentlines)
                f.close
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)
                event = {"eventtype": "conf",
                         "filepath": filepath}
                self.statechglogger.recordchgevent(myid, event)
                self.statechglogger.recordfilechange(filepath, tmppath, myid)
                os.rename(tmppath, filepath)
                os.chown(filepath, 0, 0)
                os.chmod(filepath, 420)
                resetsecon(filepath)
                appended = True

            self.logger.log(LogPriority.DEBUG, "Appended correct config line to file " + str(filepath))

        except Exception:
            raise
        return appended
