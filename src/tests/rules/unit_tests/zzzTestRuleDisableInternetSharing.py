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
This is a Unit Test for Rule ConfigureLoginWindow

@author: ekkehard j. koch
@change: 02/27/2013 Original Implementation
'''
from __future__ import absolute_import
import unittest
from src.tests.lib.RuleTestTemplate import RuleTest
from src.stonix_resources.CommandHelper import CommandHelper
from src.tests.lib.logdispatcher_mock import LogPriority
from src.stonix_resources.rules.DisableInternetSharing import DisableInternetSharing


class zzzTestRuleDisableInternetSharing(RuleTest):

    def setUp(self):
        RuleTest.setUp(self)
        self.rule = DisableInternetSharing(self.config, self.environ,
                                                 self.logdispatch,
                                                 self.statechglogger)
        self.rulename = self.rule.rulename
        self.rulenumber = self.rule.rulenumber
        self.ch = CommandHelper(self.logdispatch)
        self.dc = "/usr/bin/defaults"

    def tearDown(self):
        pass

    def runTest(self):
        self.simpleRuleTest()

    def setConditionsForRule(self):
        '''
        This makes sure the intial report fails by executing the following
        commands:
        defaults -currentHost write /Library/Preferences/SystemConfiguration/com.apple.nat NAT -dict Enabled -int 1
        @param self: essential if you override this definition
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        success = True
        if success:
            command = [self.dc, "-currentHost", "write",
                       "/Library/Preferences/SystemConfiguration/com.apple.nat",
                       "NAT", "-dict", "Enabled", "-int", "1"]
            self.logdispatch.log(LogPriority.DEBUG, str(command))
            success = self.ch.executeCommand(command)
        if success:
            success = self.checkReportForRule(False, True)
        return success

    def checkReportForRule(self, pCompliance, pRuleSuccess):
        '''
        To see what happended run these commans:
        defaults -currentHost read /Library/Preferences/SystemConfiguration/com.apple.nat NAT
        @param self: essential if you override this definition
        @return: boolean - If successful True; If failure False
        @author: ekkehard j. koch
        '''
        self.logdispatch.log(LogPriority.DEBUG, "pCompliance = " + \
                             str(pCompliance) + ".")
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
                             str(pRuleSuccess) + ".")
        success = True
        if success:
            command = [self.dc, "-currentHost", "read",
                       "/Library/Preferences/SystemConfiguration/com.apple.nat",
                       "NAT"]
            self.logdispatch.log(LogPriority.DEBUG, str(command))
            success = self.ch.executeCommand(command)
        return success

    def checkFixForRule(self, pRuleSuccess):
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
                             str(pRuleSuccess) + ".")
        success = self.checkReportForRule(True, pRuleSuccess)
        return success

    def checkUndoForRule(self, pRuleSuccess):
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
                             str(pRuleSuccess) + ".")
        success = self.checkReportForRule(False, pRuleSuccess)
        return success

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
