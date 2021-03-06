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
Created on Oct 27, 2011
The DisableAutoLogin object is responsible for disabling auto-login on
the system.  This rule is specific to Mac systems.

@operating system: Mac OS X
@author: Roy Nielsen
@change: 02/13/2014 ekkehard Implemented self.detailedresults flow
@change: 02/13/2014 ekkehard Implemented isapplicable
@change: 2014/10/17 ekkehard OS X Yosemite 10.10 Update
@change: 2015/04/14 dkennel updated for new isApplicable
@change: 2015/10/07 eball Help text/PEP8 cleanup

'''
from __future__ import absolute_import
import re
import traceback

# The period was making python complain. Adding the correct paths to PyDev
# made this the working scenario.
from ..ruleKVEditor import RuleKVEditor
from ..filehelper import FileHelper
from ..CommandHelper import CommandHelper
from ..logdispatcher import LogPriority


class DisableAutoLogin(RuleKVEditor):
    """
    This class disables Auto Login on the system.
    """
    def __init__(self, config, environ, logdispatcher, statechglogger):
        '''
        Constructor
        '''
        RuleKVEditor.__init__(self, config, environ, logdispatcher,
                              statechglogger)
        self.rulenumber = 169
        self.rulename = 'DisableAutoLogin'
        self.formatDetailedResults("initialize")
        self.applicable = {'type': 'white',
                           'os': {'Mac OS X': ['10.9', 'r', '10.11.10']}}
        self.mandatory = True
        self.helptext = "This rule will disable auto login on this " + \
            "computer. This cannot be undone/reverted."
        self.rootrequired = True
        self.files = {"kcpassword": {"path": "/etc/kcpassword",
                                     "remove": True,
                                     "content": None,
                                     "permissions": None,
                                     "owner": None,
                                     "group": None,
                                     "eventid":
                                     str(self.rulenumber).zfill(4) +
                                     "kcpassword"}}
        self.addKVEditor("DisableAutoLogin",
                         "defaults",
                         "/Library/Preferences/com.apple.loginwindow",
                         "",
                         {"autoLoginUser": [re.escape("The domain/default pair of (/Library/Preferences/com.apple.loginwindow, autoLoginUser) does not exist"), None]},
                         "present",
                         "",
                         "This variable is to determine whether or not to " +
                         "disable auto login",
                         None,
                         False,
                         {})
        self.fh = FileHelper(self.logdispatch, self.statechglogger)
        self.ch = CommandHelper(self.logdispatch)
        for filelabel, fileinfo in sorted(self.files.items()):
            self.fh.addFile(filelabel,
                            fileinfo["path"],
                            fileinfo["remove"],
                            fileinfo["content"],
                            fileinfo["permissions"],
                            fileinfo["owner"],
                            fileinfo["group"],
                            fileinfo["eventid"])

    def report(self):
        '''
        Report on the status of this rule

        @author: Roy Nielsen
        '''
        try:
            self.detailedresults = ""
            self.kvcompliant = False
            self.fhcompliant = False
            self.kvcompliant = RuleKVEditor.report(self)
            if not self.kvcompliant:
                self.detailedresults = "DisableAutoLogin is not compliant!"
            else:
                self.detailedresults = "DisableAutoLogin is compliant!"
            self.fhcompliant = self.fh.evaluateFiles()
            if not self.fhcompliant:
                self.detailedresults = self.detailedresults + "\n" + \
                    self.fh.getFileMessage()
            if not self.fhcompliant or not self.kvcompliant:
                self.compliant = False
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, err:
            self.rulesuccess = False
            self.detailedresults = self.detailedresults + "\n" + str(err) + \
                " - " + str(traceback.format_exc())
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("report", self.compliant,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return self.compliant

    def fix(self):
        '''
        Disables Auto Login

        @author: Roy Nielsen
        '''
        try:
            self.detailedresults = ""
            fixed = False
            self.kvfix = False
            self.fhfix = False
            self.kvfix = RuleKVEditor.fix(self)
            if self.kvfix:
                self.fhfix = self.fh.fixFiles()
                if self.fhfix:
                    self.detailedresults = self.detailedresults + "\n" + \
                        self.fh.getFileMessage()
            if not self.kvfix or not self.fhfix:
                fixed = False
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception, err:
            self.rulesuccess = False
            self.detailedresults = self.detailedresults + "\n" + str(err) + \
                " - " + str(traceback.format_exc())
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", fixed,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return fixed
