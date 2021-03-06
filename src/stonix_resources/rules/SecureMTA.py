'''
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
Created on Aug 8, 2013

Mail servers are used to send and receive mail over a network on behalf of site
users. Mail is a very common service, and MTAs are frequent targets of network
attack. Ensure that machines are not running MTAs unnecessarily, and configure
needed MTAs as defensively as possible.

@author: Breen Malmberg
@change: 02/03/2014 dwalker revised
@change: 02/16/2014 ekkehard Implemented self.detailedresults flow
@change: 02/16/2014 ekkehard Implemented isapplicable
@change: 04/21/2014 dkennel Updated CI invocation
@change: 2014/07/29 dkennel Fixed multiple calls to setPerms where 6 args were
given instead of the required five.
@change: 2014/08/11 ekkehard fixed isApplicable
@change: 03/4/2015 dwalker added new directive to dictionary
@change: 2015/04/17 dkennel updated for new isApplicable
@change: 2015/04/28 dkennel changed data dictionary in reportpostfix to
reference localize.py MAILRELAYSERVER instead of static local value.
@change: 2015/07/30 eball Changed where setPerms occurs in fix
@change: 2015/10/08 eball Help text cleanup
@change: 2015/11/09 ekkehard - make eligible of OS X El Capitan
'''

from __future__ import absolute_import
from ..rule import Rule
from ..stonixutilityfunctions import resetsecon, readFile, iterate, setPerms
from ..stonixutilityfunctions import checkPerms, writeFile
from ..logdispatcher import LogPriority
from ..pkghelper import Pkghelper
from ..KVEditorStonix import KVEditorStonix
from ..localize import MAILRELAYSERVER
import os
import traceback
import re


class SecureMTA(Rule):
    '''
    Mail servers are used to send and receive mail over a network on behalf of
site users. Mail is a very common service, and MTAs are frequent targets of
network attack. Ensure that machines are not running MTAs unnecessarily, and
configure needed MTAs as defensively as possible.
    '''

    def __init__(self, config, environ, logger, statechglogger):
        Rule.__init__(self, config, environ, logger, statechglogger)
        self.logger = logger
        self.rulenumber = 53
        self.rulename = 'SecureMTA'
        self.formatDetailedResults("initialize")
        self.mandatory = True
        self.rulesuccess = True
        self.helptext = '''Mail servers are used to send and receive mail \
over a network on behalf of site users. Mail is a very common service, and \
MTAs are frequent targets of network attack. Ensure that machines are not \
running MTAs unnecessarily, and configure needed MTAs as defensively as \
possible.
Please be advised, in one section of this rule, the \
/etc/mail/sendmail.cf is modified two different times.  Because of this, the \
undo event that handles this file if a change is made will only revert one \
change, the change that is not reverted is the insertion or modification of \
the line that begins with DS.  If you can't remember the original format of \
that line, take a look in the /usr/share/stonix folder for the original file \
before clicking undo.'''
        self.guidance = ['CCE 4416-4', 'CCE 4663-1', 'CCE 14495-6',
                         'CCE 14068-1', 'CCE 15018-5', 'CCE 4293-7']
        self.applicable = {'type': 'white',
                           'family': ['linux', 'solaris', 'freebsd'],
                           'os': {'Mac OS X': ['10.9', 'r', '10.11.10']}}

        self.postfixfoundlist = []
        self.sendmailfoundlist = []

        datatype = 'bool'
        key = 'SECUREMTA'
        instructions = '''To prevent the configuration of the mail transfer
agent, set the value of SECUREMTA to False.'''
        default = True
        self.mta = self.initCi(datatype, key, instructions, default)
        self.mta.setsimple(True)

        self.iditerator = 0
        self.ds = True
        self.sndmailed = None
        self.postfixed = None
        self.postfixpathlist = ['/etc/postfix/main.cf',
                                '/private/etc/postfix/main.cf',
                                '/usr/lib/postfix/main.cf']
        self.postfixpath = ''
        for path in self.postfixpathlist:
            if os.path.exists(path):
                self.postfixpath = path

    def report(self):
        '''
        The report method examines the current configuration and determines
        whether or not it is correct. If the config is correct then the
        self.compliant, self.detailed results and self.currstate properties are
        updated to reflect the system status. self.rulesuccess will be updated
        if the rule does not succeed.

        @return self.compliant
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/22/2015 - full refactor
        '''

        self.compliant = True
        self.postfixfoundlist = []
        self.detailedresults = ""
        self.postfixlist = ['postfix', 'squeeze', 'squeeze-backports',
               'wheezy', 'jessie', 'sid', 'CNDpostfix', 'lucid',
               'lucid-updates', 'lucid-backports', 'precise',
               'precise-updates', 'quantal', 'quantal-updates',
               'raring', 'saucy', 'wheezy-backports', 'postfix-current',
               'trusty', 'trusty-updates', 'vivid', 'wily', 'xenial']
        self.postfixinstalled = False
        self.sendmailinstalled = False

        try:

            # instantiate pkghelper object instance only if system is not a mac
            if not self.environ.operatingsystem == "Mac OS X":
                self.helper = Pkghelper(self.logger, self.environ)

                # check for installed versions of postfix on this system
                # check for installed sendmail on this system
                for item in self.postfixlist:
                    if self.helper.check(item):
                        self.postfixinstalled = True
                        self.postfixfoundlist.append(item)
                if self.helper.check('sendmail'):
                    self.sendmailinstalled = True

                # if sendmail installed, run check on sendmail configuration
                if self.sendmailinstalled:
                    if not self.reportsendmail():
                        self.compliant = False

                # if postfix installed, run check on postfix configuration
                if self.postfixinstalled:
                    if not self.reportpostfix():
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

###############################################################################
    def reportsendmail(self):
        '''
        Check config of sendmail

        @return retval
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/22/2015 - refactored method
        '''

        retval = True
        path = '/etc/mail/sendmail.cf'
        tpath = path + '.tmp'
        kvtype = 'conf'
        conftype = 'closedeq'
        intent = 'present'
        data = {"O SmtpGreetingMessage": "", "O PrivacyOptions": "goaway"}

        try:

            if not os.path.exists(path):
                self.detailedresults += '\nUnable to locate sendmail configuration file.'
                retval = False
                return retval

            # create the kveditor object
            self.sndmailed = KVEditorStonix(self.statechglogger, self.logger,
                                            kvtype, path, tpath, data, intent,
                                            conftype)

            # use kveditor to search the conf file for all the options in postfix data
            if not self.sndmailed.report():
                self.detailedresults += "Not all directives were found inside " + str(path) + " file\n"
                retval = False

            if os.path.exists(path):
                # check permissions on sendmail configuration file
                if not checkPerms(path, [0, 0, 420], self.logger):
                    self.detailedresults += "File: " + str(path) + " has incorrect permissions."
                # check runtogether keyvalues; may replace with kveditor later if
                # kveditor gets updated to handle runtogether keyvalues
                contents = readFile(path, self.logger)
                found = False
                for line in contents:
                    if re.search('^DS', line):
                        found = True
                        if not re.search('^DS' + MAILRELAYSERVER, line):
                            self.detailedresults += "\nDS line doesn't have correct contents inside " + path + " file."
                            self.ds = True
                            retval = False
                if not found:
                    self.detailedresults += "DS line not found in " + str(path) + " file \n"
                    self.ds = True
                    retval = False

        except Exception:
            raise
        return retval

###############################################################################
    def reportpostfix(self):
        '''
        Check config of postfix

        @return retval
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/22/2015 - refactored method
        '''

        retval = True
        data = {'inet_interfaces': 'localhost',
                'default_process_limit': '100',
                'smtpd_client_connection_count_limit': '10',
                'smtpd_client_connection_rate_limit': '30',
                'queue_minfree': '20971520',
                'header_size_limit': '51200',
                'message_size_limit': '10485760',
                'smtpd_recipient_limit': '100',
                'smtpd_banner': '$myhostname ESMTP',
                'mynetworks_style': 'host',
                'smtpd_recipient_restrictions':
                'permit_mynetworks, reject_unauth_destination',
                'relayhost': MAILRELAYSERVER}

        kvtype = 'conf'
        conftype = 'openeq'
        intent = 'present'

        for path in self.postfixpathlist:
            if os.path.exists(path):
                self.postfixpath = path
        tpath = self.postfixpath + '.tmp'

        try:

            if not self.postfixpath:
                self.detailedresults += '\nCould not locate postfix configuration file.'
                retval = False
                return retval

            # create the kveditor object
            self.postfixed = KVEditorStonix(self.statechglogger, self.logger,
                                            kvtype, self.postfixpath, tpath, data,
                                            intent, conftype)

            # check permissions on postfix configuration file
            if os.path.exists(self.postfixpath):
                if not checkPerms(self.postfixpath, [0, 0, 420], self.logger):
                    self.detailedresults += "\nFile: " + str(self.postfixpath) + " has incorrect permissions."
                    retval = False

            # use kveditor to search the conf file for all the options in postfix data
            if not self.postfixed.report():
                self.detailedresults += "\nNot all directives were found in " + str(self.postfixpath) + " file."
                retval = False

        except Exception:
            raise
        return retval

###############################################################################
    def fix(self):
        '''
        Call either fixpostfix() or fixsendmail() depending on which one is
        installed.

        @return: fixsuccess
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/22/2015 - refactored method
        '''

        self.logger.log(LogPriority.DEBUG, "Inside main fix() method")
        self.logger.log(LogPriority.DEBUG, "Setting method variable defaults...")
        self.detailedresults = ""
        fixsuccess = True
        self.iditerator = 0

        try:

            self.logger.log(LogPriority.DEBUG, "Checking value of CI...")

            # if nothing is selected, just exit and inform user
            if not self.mta.getcurrvalue():
                self.detailedresults += '\nThe CI for this rule is currently disabled. Nothing will be done...'
                fixsuccess = True
                self.formatDetailedResults("fix", fixsuccess, self.detailedresults)
                self.logdispatch.log(LogPriority.INFO, self.detailedresults)
                return fixsuccess

            self.logger.log(LogPriority.DEBUG, "Finding and deleting old event entries...")
            # clear out event history so only the latest fix is recorded
            eventlist = self.statechglogger.findrulechanges(self.rulenumber)
            for event in eventlist:
                self.statechglogger.deleteentry(event)

            # if the kveditor object for postfix exists, then run the fix postfix method
            if self.postfixed:
                self.logger.log(LogPriority.DEBUG, "Running fixpostfix() method...")
                if not self.fixpostfix():
                    fixsuccess = False
                    self.detailedresults += '\nThe fix for postfix failed.'

            # if the kveditor object for sendmail exists, then run the fix sendmail method
            if self.sndmailed:
                self.logger.log(LogPriority.DEBUG, "Running fixsendmail() method...")
                if not self.fixsendmail():
                    fixsuccess = False
                    self.detailedresults += '\nThe fix for sendmail failed.'

            elif self.ds:
                if os.path.exists('/etc/mail/sendmail.cf'):
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    if not setPerms("/etc/mail/sendmail.cf", [0, 0, 420], self.logger, self.statechglogger, myid):
                        fixsuccess = False
                        self.detailedresults += '\nCould not correctly set permissions on file: /etc/mail/sendmail.cf'
                if not self.fixsendmail():
                    fixsuccess = False
                    self.detailedresults += '\nThe fix for sendmail failed.'

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", fixsuccess, self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return fixsuccess

###############################################################################
    def fixpostfix(self):
        '''
        Configure the postfix client securely if installed.

        @return: retval
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/22/2015 - completely refactored method
        '''

        retval = True

        try:

            if not self.postfixinstalled:
                self.detailedresults += '\nNo mail transfer agent detected. Nothing to do...'
                retval = True
                return retval

            self.iditerator += 1
            myid = iterate(self.iditerator, self.rulenumber)
            self.postfixed.setEventID(myid)

            if not self.postfixed.fix():
                debug = "kveditor fix did not run successfully, returning"
                self.logger.log(LogPriority.DEBUG, debug)
                self.detailedresults += '\nkveditor failed to run fix method'
                retval = False
                return retval
            elif not self.postfixed.commit():
                debug = "kveditor commit did not run successfully, returning"
                self.logger.log(LogPriority.DEBUG, debug)
                self.detailedresults += '\nkveditor failed to commit changes'
                retval = False
                return retval

            if os.path.exists(self.postfixpath):
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)
                if not setPerms(self.postfixpath, [0, 0, 420], self.logger, self.statechglogger, myid):
                    retval = False
                    self.detailedresults += '\nCould not correctly set permissions on file: ' + str(self.postfixpath)
            else:
                self.detailedresults += '\nPostfix is installed, but could not locate postfix configuration file.'
                retval = False
                return retval

        except Exception:
            raise
        return True

###############################################################################
    def fixsendmail(self):
        '''
        Configure the sendmail client securely if installed.

        @return: success
        @rtype: bool
        @author Breen Malmberg
        @change: dwalker - ??? - ???
        @change: Breen Malmberg - 12/21/2015 - corrected the check to see if sendmail is installed but missing a config file;
                                                added user messaging to let the user know what is wrong;
                                                partial refactor of method
        '''

        self.logger.log(LogPriority.DEBUG, "Inside fixsendmail() method")
        self.logger.log(LogPriority.DEBUG, "Setting method variables to defaults...")
        success = True
        path = "/etc/mail/sendmail.cf"

        try:

            self.logger.log(LogPriority.DEBUG, "Checking if sendmail package is installed...")
            if not self.helper.check('sendmail'):
                self.detailedresults += '\nSendmail is not installed.. no need to configure it.'
                success = True
                return success

            elif not os.path.exists('/etc/mail'):
                os.makedirs('/etc/mail', 0755)

            if self.sndmailed and os.path.exists(path):

                if self.sndmailed.fixables:
                    if self.ds:
                        tpath = path + ".tmp"
                        contents = readFile(path, self.logger)
                        tempstring = ""
                        for line in contents:
                            if re.search("^DS(.)*", line):
                                continue
                            else:
                                tempstring += line
                        tempstring += "DS" + MAILRELAYSERVER + "\n"
                        if writeFile(tpath, tempstring, self.logger):
                            os.rename(tpath, path)
                            os.chown(path, 0, 0)
                            os.chmod(path, 420)
                            resetsecon(path)
                        else:
                            success = False
                            self.detailedresults += '\nUnable to write changes to file: ' + str(tpath)

                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    self.sndmailed.setEventID(myid)
                    self.sndmailed.setPath(path)

                    if not self.sndmailed.fix():
                        debug = "kveditor fix did not run successfully, returning"
                        self.logger.log(LogPriority.DEBUG, debug)
                        self.detailedresults += '\n' + debug
                        success = False
                    if not self.sndmailed.commit():
                        debug = "kveditor fix did not run successfully, returning"
                        self.logger.log(LogPriority.DEBUG, debug)
                        self.detailedresults += '\n' + debug
                        success = False
                    else:
                        os.chown(path, 0, 0)
                        os.chmod(path, 420)
                        resetsecon(path)

                else:

                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    if not setPerms(path, [0, 0, 420], self.logger, self.statechglogger, myid):
                        success = False
                        self.detailedresults += '\nUnable to set permissions correctly on file: ' + str(path)

            elif self.ds and os.path.exists(path):
                tpath = path + ".tmp"
                contents = readFile(path, self.logger)
                tempstring = ""
                for line in contents:
                    if re.search("^DS(.)*", line):
                        continue
                    else:
                        tempstring += line
                tempstring += "DS" + MAILRELAYSERVER
                self.iditerator += 1
                myid = iterate(self.iditerator, self.rulenumber)

                if writeFile(tpath, tempstring, self.logger):
                    event = {"eventtype": "conf",
                             "filepath": path,
                             "id": myid}
                    self.statechglogger.recordchgevent(myid, event)
                    self.statechglogger.recordfilechange(path, tpath, myid)
                    os.rename(tpath, path)
                    os.chown(path, 0, 0)
                    os.chmod(path, 420)
                    resetsecon(path)
                else:
                    success = False
                    self.detailedresults += '\nUnable to write changes to file: ' + str(tpath)
            else:
                self.detailedresults += '\nSendmail configuration file not in expected location, or does not exist. Will not attempt to create this file. Removing sendmail package...'
                self.helper.remove('sendmail')
                success = True

        except Exception:
            raise
        return success
