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
This is a Unit Test for Rule SSHTimeout

@author: Eric Ball
@change: 2015/09/24 eball Original Implementation
'''
from __future__ import absolute_import
import unittest
import os
from src.tests.lib.RuleTestTemplate import RuleTest
from src.stonix_resources.CommandHelper import CommandHelper
from src.stonix_resources.KVEditorStonix import KVEditorStonix
from src.stonix_resources.stonixutilityfunctions import setPerms, iterate
from src.tests.lib.logdispatcher_mock import LogPriority
from src.stonix_resources.rules.SSHTimeout import SSHTimeout


class zzzTestRuleSSHTimeout(RuleTest):

    def setUp(self):
        RuleTest.setUp(self)
        self.rule = SSHTimeout(self.config,
                               self.environ,
                               self.logdispatch,
                               self.statechglogger)
        self.rulename = self.rule.rulename
        self.rulenumber = self.rule.rulenumber
        self.ch = CommandHelper(self.logdispatch)

    def tearDown(self):
        pass

    def runTest(self):
        self.simpleRuleTest()

    def setConditionsForRule(self):
        '''
        Configure system for the unit test
        @param self: essential if you override this definition
        @return: boolean - If successful True; If failure False
        @author: Eric Ball
        '''
        success = True
        # Run report() to get variables
        self.rule.report()
        ssh = {"ClientAliveInterval": "0",
               "ClientAliveCountMax": "900"}
        if os.path.exists(self.rule.path):
            kvtype = "conf"
            intent = "present"
            self.editor = KVEditorStonix(self.statechglogger, self.logdispatch,
                                         kvtype, self.rule.path,
                                         self.rule.tpath, ssh, intent, "space")
            if not self.editor.report():
                if self.editor.fixables:
                    if self.editor.fix():
                        if not self.editor.commit():
                            success = False
                            debug = "KVEditor commit did not succeed"
                            self.logdispatch.log(LogPriority.DEBUG, debug)
                    else:
                        success = False
                        debug = "KVEditor fix() did not succeed"
                        self.logdispatch.log(LogPriority.DEBUG, debug)
            self.rule.iditerator = 0
            myid = iterate(self.rule.iditerator, self.rule.rulenumber)
            if not setPerms(self.rule.path, [99, 99, 0770], self.logdispatch,
                            self.statechglogger, myid):
                success = False
                debug = "Could not set permissions"
                self.logdispatch.log(LogPriority.DEBUG, debug)
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
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
