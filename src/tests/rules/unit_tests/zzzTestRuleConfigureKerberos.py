#!/usr/bin/env python
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
This is a Unit Test for Rule ConfigureAppleSoftwareUpdate

@author: ekkehard j. koch
@change: 04/02/2013 Original Implementation
@change: 07/14/2014 - ekkehard - made testing more rigorous
@change: 07/28/2014 - ekkehard - bug fixes
@change: 2015/12/18 - eball - Added eventids
'''
from __future__ import absolute_import
import unittest
from src.tests.lib.RuleTestTemplate import RuleTest
from src.stonix_resources.CommandHelper import CommandHelper
from src.stonix_resources.filehelper import FileHelper
from src.tests.lib.logdispatcher_mock import LogPriority
from src.stonix_resources.rules.ConfigureKerberos import ConfigureKerberos


class zzzTestRuleConfigureKerberos(RuleTest):

    def setUp(self):
        RuleTest.setUp(self)
        self.rule = ConfigureKerberos(self.config,
                                      self.environ,
                                      self.logdispatch,
                                      self.statechglogger)
        self.rulename = self.rule.rulename
        self.rulenumber = self.rule.rulenumber
        self.ch = CommandHelper(self.logdispatch)
        self.fh = FileHelper(self.logdispatch, self.statechglogger)
        if self.environ.getosfamily() == 'darwin':
            self.files = {"kerb5.conf":
                          {"path": "/etc/krb5.conf",
                           "remove": True,
                           "content": None,
                           "permissions": None,
                           "owner": None,
                           "group": None,
                           "eventid": str(self.rulenumber).zfill(4) +
                           "kerb5ut"},
                          "edu.mit.Kerberos":
                          {"path": "/Library/Preferences/edu.mit.Kerberos",
                           "remove": False,
                           "content": "test",
                           "permissions": None,
                           "owner": None,
                           "group": None,
                           "eventid": str(self.rulenumber).zfill(4) +
                           "Kerberosut"},
                          "edu.mit.Kerberos.krb5kdc.launchd":
                          {"path": "/Library/Preferences/edu.mit.Kerberos.krb5kdc.launchd",
                           "remove": False,
                           "content": "test",
                           "permissions": None,
                           "owner": None,
                           "group": None,
                           "eventid": str(self.rulenumber).zfill(4) +
                           "krb5kdcut"},
                          "edu.mit.Kerberos.kadmind.launchd":
                          {"path": "/Library/Preferences/edu.mit.Kerberos.kadmind.launchd",
                           "remove": False,
                           "content": "test",
                           "permissions": None,
                           "owner": None,
                           "group": None,
                           "eventid": str(self.rulenumber).zfill(4) +
                           "kadmindut"},
                        }
        else:
            self.files = {"kerb5.conf":
                          {"path": "/etc/krb5.conf",
                           "remove": True,
                           "content": None,
                           "permissions": None,
                           "owner": None,
                           "group": None,
                           "eventid": str(self.rulenumber).zfill(4) +
                           "kerb5ut"}}

    def tearDown(self):
        pass

    def runTest(self):
        self.simpleRuleTest()

    def setConditionsForRule(self):
        '''
        Configure system for the unit test
        @param self: essential if you override this definition
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        for filelabel, fileinfo in sorted(self.files.items()):
            self.fh.addFile(filelabel,
                            fileinfo["path"],
                            fileinfo["remove"],
                            fileinfo["content"],
                            fileinfo["permissions"],
                            fileinfo["owner"],
                            fileinfo["group"],
                            fileinfo["eventid"])

        success = self.fh.fixFiles()
        return success

    def checkReportForRule(self, pCompliance, pRuleSuccess):
        '''
        check on whether report was correct
        @param self: essential if you override this definition
        @param pCompliance: the self.iscompliant value of rule
        @param pRuleSuccess: did report run successfully
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        self.logdispatch.log(LogPriority.DEBUG, "pCompliance = " +
                             str(pCompliance) + ".")
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " +
                             str(pRuleSuccess) + ".")
        success = True
        return success

    def checkFixForRule(self, pRuleSuccess):
        '''
        check on whether fix was correct
        @param self: essential if you override this definition
        @param pRuleSuccess: did report run successfully
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " +
                             str(pRuleSuccess) + ".")
        success = True
        return success

    def checkUndoForRule(self, pRuleSuccess):
        '''
        check on whether undo was correct
        @param self: essential if you override this definition
        @param pRuleSuccess: did report run successfully
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " +
                             str(pRuleSuccess) + ".")
        success = True
        return success

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
