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
@change: 03/26/2013 Original Implementation
'''
from __future__ import absolute_import
import unittest
from src.tests.lib.RuleTestTemplate import RuleTest
from src.stonix_resources.CommandHelper import CommandHelper
from src.tests.lib.logdispatcher_mock import LogPriority
from src.stonix_resources.rules.ConfigureScreenLocking import ConfigureScreenLocking


class zzzTestRuleConfigureScreenLocking(RuleTest):

    def setUp(self):
        RuleTest.setUp(self)
        self.rule = ConfigureScreenLocking(self.config,
                                           self.environ,
                                           self.logdispatch,
                                           self.statechglogger)
        self.rulename = self.rule.rulename
        self.rulenumber = self.rule.rulenumber
        self.effectiveUserID = self.environ.geteuid()
        self.ch = CommandHelper(self.logdispatch)
        self.dc = "/usr/bin/defaults"

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
        success = True
        if self.environ.getosfamily() == "darwin":
            if self.effectiveUserID == 0:
                if success:
                    command = [self.dc, "-currentHost", "delete",
                               "/Library/Preferences/com.apple.screensaver",
                               "askForPassword"]
                    self.logdispatch.log(LogPriority.DEBUG, str(command))
                    success = self.ch.executeCommand(command)
                if success:
                    command = [self.dc, "-currentHost", "delete",
                               "/Library/Preferences/com.apple.screensaver",
                               "idleTime"]
                    self.logdispatch.log(LogPriority.DEBUG, str(command))
                    success = self.ch.executeCommand(command)
                if success:
                    command = [self.dc, "-currentHost", "delete",
                               "/Library/Preferences/com.apple.screensaver",
                               "loginWindowIdleTime"]
                    self.logdispatch.log(LogPriority.DEBUG, str(command))
                    success = self.ch.executeCommand(command)
            else:
                if success:
                    command = [self.dc, "-currentHost", "delete",
                               "~/Library/Preferences/com.apple.screensaver",
                               "askForPassword"]
                    self.logdispatch.log(LogPriority.DEBUG, str(command))
                    success = self.ch.executeCommand(command)
                if success:
                    command = [self.dc, "-currentHost", "delete",
                               "~/Library/Preferences/com.apple.screensaver",
                               "askForPasswordDelay"]
                    self.logdispatch.log(LogPriority.DEBUG, str(command))
                    success = self.ch.executeCommand(command)
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
        self.logdispatch.log(LogPriority.DEBUG, "pCompliance = " + \
                             str(pCompliance) + ".")
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
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
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
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
        self.logdispatch.log(LogPriority.DEBUG, "pRuleSuccess = " + \
                             str(pRuleSuccess) + ".")
        success = True
        return success

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
