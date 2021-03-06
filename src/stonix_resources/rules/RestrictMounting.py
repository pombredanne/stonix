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
This rule restricts mounting rights and options.

@author: Eric Ball
@change: 2015-07-06 eball Original implementation
'''
from __future__ import absolute_import
import os
import re
import traceback
from ..stonixutilityfunctions import iterate, resetsecon
from ..stonixutilityfunctions import writeFile, readFile
from ..rule import Rule
from ..logdispatcher import LogPriority
from ..CommandHelper import CommandHelper
from ..KVEditorStonix import KVEditorStonix
from ..pkghelper import Pkghelper
from ..ServiceHelper import ServiceHelper


class RestrictMounting(Rule):

    def __init__(self, config, enviro, logger, statechglogger):
        Rule.__init__(self, config, enviro, logger, statechglogger)
        self.logger = logger
        self.rulenumber = 112
        self.rulename = "RestrictMounting"
        self.formatDetailedResults("initialize")
        self.mandatory = False
        self.helptext = '''This optional rule can be used to restrict access \
and permissions related to disk mounts.\nRESTRICTCONSOLEACCESS will restrict \
device ownership for console users to root only.\nDISABLEAUTOFS disables the \
autofs service, which is used to dynamically mount NFS filesystems. Even if \
NFS in needed, NFS filesystems can usually be statically mounted through
/etc/fstab.\nDISABLEGNOMEAUTOMOUNT will restrict the gnome-volume-manager \
(part of the GNOME Desktop Environment) from automatically mounting devices \
and media.'''

        # Configuration item instantiation
        datatype = "bool"
        key = "RESTRICTCONSOLEACCESS"
        instructions = "To restrict console device access, set " + \
                       "RESTRICTCONSOLEACCESS to True."
        default = False
        self.consoleCi = self.initCi(datatype, key, instructions, default)

        key = "DISABLEAUTOFS"
        instructions = "To disable dynamic NFS mounting through the " + \
                       "autofs service, set DISABLEAUTOFS to True."
        self.autofsCi = self.initCi(datatype, key, instructions, default)

        key = "DISABLEGNOMEAUTOMOUNT"
        instructions = "To disable the GNOME desktop environment from " + \
                       "automounting devices and removable media, set " + \
                       "DISABLEGNOMEAUTOMOUNT to True."
        self.gnomeCi = self.initCi(datatype, key, instructions, default)

        self.guidance = ["NSA 2.2.2.1", "NSA 2.2.2.3", "NSA 2.2.2.4",
                         "CCE 3685-5", "CCE 4072-5", "CCE 4231-7"]
        self.applicable = {"type": "white",
                           "family": ["linux"]}
        self.iditerator = 0

    def report(self):
        try:
            self.path1 = "/etc/security/console.perms.d/50-default.perms"
            self.path2 = "/etc/security/console.perms"
            self.data = {"<console>":
                         "tty[0-9][0-9]* vc/[0-9][0-9]* :0\.[0-9] :0",
                         "<xconsole>": "0\.[0-9] :0"}
            self.ph = Pkghelper(self.logdispatch, self.environ)
            self.sh = ServiceHelper(self.environ, self.logdispatch)
            self.ch = CommandHelper(self.logdispatch)
            compliant = True
            results = ""

            if os.path.exists(self.path1):
                defaultPerms = readFile(self.path1, self.logger)
                for line in defaultPerms:
                    if re.search("^<[x]?console>", line, re.M):
                        compliant = False
                        results += self.path1 + " contains " + \
                                                "unrestricted device access\n"
                        break

            if os.path.exists(self.path2):
                self.tmppath = self.path2 + ".tmp"
                self.editor = KVEditorStonix(self.statechglogger, self.logger,
                                             "conf", self.path2, self.tmppath,
                                             self.data, "present", "closedeq")
                kveReport = self.editor.report()
                if not kveReport:
                    compliant = False
                    results += self.path2 + " does not contain " + \
                                            "the correct values\n"

            if self.ph.check("autofs"):
                if self.sh.auditservice("autofs"):
                    compliant = False
                    results += "autofs is installed and enabled\n"

            if os.path.exists("/usr/bin/gconftool-2"):
                cmd = ["gconftool-2", "-R", "/desktop/gnome/volume_manager"]
                self.ch.executeCommand(cmd)
                gconf = self.ch.getOutputString()
                if len(re.findall("automount_[media|drives]+ = false", gconf)) < 2:
                    compliant = False
                    results += "GNOME automounting is not disabled\n"

            self.compliant = compliant
            if self.compliant:
                self.detailedresults = "RestrictMounting report has been " + \
                    "run and is compliant"
            else:
                self.detailedresults = "RestrictMounting report has been " + \
                    "run and is not compliant\n" + results
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

    def fix(self):
        try:
            if not self.consoleCi.getcurrvalue() and \
               not self.autofsCi.getcurrvalue() and \
               not self.gnomeCi.getcurrvalue():
                return
            success = True
            results = ""
            self.iditerator = 0
            eventlist = self.statechglogger.findrulechanges(self.rulenumber)
            for event in eventlist:
                self.statechglogger.deleteentry(event)

            if self.consoleCi.getcurrvalue():
                if os.path.exists(self.path1):
                    tmpfile = self.path1 + ".tmp"
                    defaultPerms = open(self.path1, "r").read()
                    defaultPerms = re.sub("(<[x]?console>)", r"#\1",
                                          defaultPerms)
                    if writeFile(tmpfile, defaultPerms, self.logger):
                        self.iditerator += 1
                        myid = iterate(self.iditerator, self.rulenumber)
                        event = {"eventtype": "conf", "filepath": self.path1}
                        self.statechglogger.recordchgevent(myid, event)
                        self.statechglogger.recordfilechange(self.path1,
                                                             tmpfile, myid)
                        os.rename(tmpfile, self.path1)
                        resetsecon(self.path1)
                    else:
                        success = False
                        results += "Problem writing new contents to " + \
                                   "temporary file"
                if os.path.exists(self.path2):
                    self.tmppath = self.path2 + ".tmp"
                    self.editor = KVEditorStonix(self.statechglogger, 
                                                 self.logger,
                                                 "conf", self.path2,
                                                 self.tmppath,
                                                 self.data, "present",
                                                 "closedeq")
                    self.editor.report()
                    if self.editor.fixables:
                        if self.editor.fix():
                            if self.editor.commit():
                                debug = self.path2 + "'s contents have been " \
                                        + "corrected\n"
                                self.logger.log(LogPriority.DEBUG, debug)
                                resetsecon(self.path2)
                            else:
                                debug = "kveditor commit not successful\n"
                                self.logger.log(LogPriority.DEBUG, debug)
                                success = False
                                results += self.path2 + \
                                           " properties could not be set\n"
                        else:
                            debug = "kveditor fix not successful\n"
                            self.logger.log(LogPriority.DEBUG, debug)
                            success = False
                            results += self.path2 + \
                                       " properties could not be set\n"

            if self.autofsCi.getcurrvalue():
                if self.ph.check("autofs"):
                    if self.sh.disableservice("autofs"):
                        debug = "autofs service successfully disabled\n"
                        self.logger.log(LogPriority.DEBUG, debug)
                        self.iditerator += 1
                        myid = iterate(self.iditerator, self.rulenumber)
                        event = {"eventtype": "servicehelper", "servicename":
                                 "autofs", "startstate": "enabled",
                                 "endstate": "disabled"}
                        self.statechglogger.recordchgevent(myid, event)
                    else:
                        success = False
                        debug = "Unable to disable autofs service\n"
                        self.logger.log(LogPriority.DEBUG, debug)

            if self.gnomeCi.getcurrvalue():
                cmd = ["gconftool-2", "--direct", "--config-source",
                       "xml:readwrite:/etc/gconf/gconf.xml.mandatory",
                       "--type", "bool", "--set",
                       "/desktop/gnome/volume_manager/automount_media",
                       "false"]
                cmdSuccess = self.ch.executeCommand(cmd)
                cmd = ["gconftool-2", "--direct", "--config-source",
                       "xml:readwrite:/etc/gconf/gconf.xml.mandatory",
                       "--type", "bool", "--set",
                       "/desktop/gnome/volume_manager/automount_drives",
                       "false"]
                cmdSuccess &= self.ch.executeCommand(cmd)
                if not cmdSuccess:
                    success = False
                    results += "Fix failed to disable GNOME automounting\n"

            self.rulesuccess = success
            if self.rulesuccess:
                self.detailedresults = "RestrictMounting fix has been run " + \
                                       "to completion\n"
            else:
                self.detailedresults = "RestrictMounting fix was unsuccessful\n" \
                                       + self.results
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", self.rulesuccess,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return self.rulesuccess
