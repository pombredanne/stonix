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

Created on Mar 11, 2015

@author: dwalker
@change: 2015/04/14 dkennel - Now using new isApplicable method
@change: 2015/07/27 eball - Added logger to setPerms call in fix()
'''
from __future__ import absolute_import
from ..stonixutilityfunctions import iterate, setPerms, checkPerms
from ..stonixutilityfunctions import createFile
from ..rule import Rule
from ..logdispatcher import LogPriority
from ..KVEditorStonix import KVEditorStonix
from ..pkghelper import Pkghelper
from ..ServiceHelper import ServiceHelper
import traceback
import os


class SecureNFS(Rule):

    def __init__(self, config, environ, logger, statechglogger):
        Rule.__init__(self, config, environ, logger, statechglogger)
        self.logger = logger
        self.rulenumber = 39
        self.rulename = "SecureNFS"
        self.formatDetailedResults("initialize")
        self.helptext = "Configures and secures NFS"
        self.applicable = {'type': 'white',
                           'family': ['linux', 'solaris', 'freebsd'],
                           'os': {'Mac OS X': ['10.9', 'r', '10.11.10']}}
        self.guidance = ["NSA(3.13.4)", "cce-4241-6", "cce-4465-1",
                         "cce-4559-1", "cce-4015-4", "cce-3667-3",
                         "cce-4310-9", "cce-4438-8", "cce-3579-0"]

        # Configuration item instantiation
        datatype = 'bool'
        key = 'SECURENFS'
        instructions = "To disable this rule set the value of SECURENFS " + \
            "to False."
        default = True
        self.ci = self.initCi(datatype, key, instructions, default)

    def report(self):
        '''
        '''

        try:
            self.detailedresults = ""
            self.compliant = True
            if self.environ.getosfamily() == "linux":
                self.ph = Pkghelper(self.logger, self.environ)

            self.sh = ServiceHelper(self.environ, self.logger)
            if self.environ.getostype() == "Mac OS X":
                nfsfile = "/etc/nfs.conf"
                data1 = {"nfs.lockd.port": "",
                         "nfs.lockd.tcp": "1",
                         "nfs.lockd.udp": "1"}
                if not self.sh.auditservice('/System/Library/LaunchDaemons/com.apple.nfsd.plist', 'com.apple.nfsd'):
                    self.compliant = True
                    self.formatDetailedResults("report", self.compliant,
                                   self.detailedresults)
                    self.logdispatch.log(LogPriority.INFO,
                                         self.detailedresults)
                    return self.compliant
            elif self.ph.manager in ("yum", "zypper"):
                nfsfile = "/etc/sysconfig/nfs"
                data1 = {"LOCKD_TCPPORT": "32803",
                         "LOCKD_UDPPORT": "32769",
                         "MOUNTD_PORT": "892",
                         "RQUOTAD_PORT": "875",
                         "STATD_PORT": "662",
                         "STATD_OUTGOING_PORT": "2020"}
                if self.ph.manager == "zypper":
                    nfspackage = "nfs-kernel-server"
                elif self.ph.manager == "yum":
                    nfspackage = "nfs-utils"
            elif self.ph.manager == "apt-get":
                nfsfile = "/etc/services"
                data1 = {"rpc.lockd": ["32803/tcp",
                                       "32769/udp"],
                         "rpc.mountd": ["892/tcp",
                                        "892/udp"],
                         "rpc.quotad": ["875/tcp",
                                        "875/udp"],
                         "rpc.statd": ["662/tcp",
                                       "662/udp"],
                         "rpc.statd-bc": ["2020/tcp",
                                          "2020/udp"]}
                nfspackage = "nfs-kernel-server"
            if self.environ.getostype() != "Mac OS X":
                if self.ph.manager in ("apt-get", "zypper", "yum"):
                    if not self.ph.check(nfspackage):
                        self.compliant = True
                        self.formatDetailedResults("report", self.compliant,
                                   self.detailedresults)
                        self.logdispatch.log(LogPriority.INFO,
                                             self.detailedresults)
                        return self.compliant
            if os.path.exists(nfsfile):
                nfstemp = nfsfile + ".tmp"
                if self.environ.getostype() == "Mac OS X":
                    self.editor1 = KVEditorStonix(self.statechglogger,
                                                  self.logger, "conf", nfsfile,
                                                  nfstemp, data1, "present",
                                                  "openeq")
                elif self.ph.manager in ("yum", "zypper"):
                    self.editor1 = KVEditorStonix(self.statechglogger,
                                                  self.logger, "conf", nfsfile,
                                                  nfstemp, data1, "present",
                                                  "closedeq")
                elif self.ph.manager == "apt-get":
                    self.editor1 = KVEditorStonix(self.statechglogger,
                                                  self.logger, "conf", nfsfile,
                                                  nfstemp, data1, "present",
                                                  "space")
                if not self.editor1.report():
                    self.detailedresults += "\nreport for editor1 is not compliant"
                    self.logger.log(LogPriority.DEBUG, self.detailedresults)
                    self.compliant = False
                if not checkPerms(nfsfile, [0, 0, 420], self.logger):
                    self.detailedresults += "\npermissions aren't correct on " + nfsfile
                    self.logger.log(LogPriority.DEBUG, self.detailedresults)
                    self.compliant = False
            else:
                self.detailedresults += "\n" + nfsfile + " doesn't exist"
                self.logger.log(LogPriority.DEBUG, self.detailedresults)
                self.compliant = False

            export = "/etc/exports"
            if os.path.exists(export):
                extemp = export + ".tmp"
                data2 = {"all_squash": "",
                         "no_root_squash": "",
                         "insecure_locks": ""}
                self.editor2 = KVEditorStonix(self.statechglogger, self.logger,
                                              "conf", export, extemp, data2,
                                              "notpresent", "space")
                if not self.editor2.report():
                    self.detailedresults += "\neditor2 report is not compliant"
                    self.logger.log(LogPriority.DEBUG, self.detailedresults)
                    self.compliant = False
                if not checkPerms(export, [0, 0, 420], self.logger):
                    self.detailedresults += "\n" + export + " file doesn't have the correct " + \
                        " permissions"
                    self.logger.log(LogPriority.DEBUG, self.detailedresults)
                    self.compliant = False
            else:
                self.detailedresults += "\n" + export + " file doesn't exist"
                self.logger.log(LogPriority.DEBUG, self.detailedresults)
                self.compliant = False
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.detailedresults += "\n" + traceback.format_exc()
            self.logger.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("report", self.compliant,
                                   self.detailedresults)
        self.logger.log(LogPriority.INFO, self.detailedresults)
        return self.compliant

###############################################################################

    def fix(self):
        '''
        '''

        try:
            if not self.ci.getcurrvalue():
                self.rulesuccess = True
                return self.rulesuccess

            self.detailedresults = ""

            # Clear out event history so only the latest fix is recorded
            self.iditerator = 0
            eventlist = self.statechglogger.findrulechanges(self.rulenumber)
            for event in eventlist:
                self.statechglogger.deleteentry(event)
            success = True
            changed1, changed2 = False, False
            installed = False
            if self.environ.getostype() == "Mac OS X":
                nfsservice = "nfsd"
                nfsfile = "/etc/nfs.conf"
                data1 = {"nfs.lockd.port": "",
                         "nfs.lockd.tcp": "1",
                         "nfs.lockd.udp": "1"}
            elif self.ph.manager in ("yum", "zypper"):
                nfsfile = "/etc/sysconfig/nfs"
                data1 = {"LOCKD_TCPPORT": "32803",
                         "LOCKD_UDPPORT": "32769",
                         "MOUNTD_PORT": "892",
                         "RQUOTAD_PORT": "875",
                         "STATD_PORT": "662",
                         "STATD_OUTGOING_PORT": "2020"}
                nfsservice = "nfs"
                if self.ph.manager == "zypper":
                    nfspackage = "nfs-kernel-server"
                elif self.ph.manager == "yum":
                    nfspackage = "nfs-utils"
            elif self.ph.manager == "apt-get":
                nfsservice = "nfs-kernel-server"
                nfspackage = "nfs-kernel-server"
                nfsfile = "/etc/services"
                data1 = {"rpc.lockd": ["32803/tcp",
                                       "32769/udp"],
                         "rpc.mountd": ["892/tcp",
                                        "892/udp"],
                         "rpc.quotad": ["875/tcp",
                                        "875/udp"],
                         "rpc.statd": ["662/tcp",
                                       "662/udp"],
                         "rpc.statd-bc": ["2020/tcp",
                                          "2020/udp"]}
            if self.environ.getostype() != "Mac OS X":
                if self.ph.manager in ("apt-get", "zypper"):
                    if not self.ph.check(nfspackage):
                        self.rulesuccess = True
                        self.formatDetailedResults("fix", self.rulesuccess,
                                   self.detailedresults)
                        self.logdispatch.log(LogPriority.INFO,
                                             self.detailedresults)
                        return self.rulesuccess
            if not os.path.exists(nfsfile):
                if createFile(nfsfile, self.logger):
                    nfstemp = nfsfile + ".tmp"
                    if self.environ.getostype() == "Mac OS X":
                        if not self.sh.auditservice('/System/Library/LaunchDaemons/com.apple.nfsd.plist', 'com.apple.nfsd'):
                            self.rulesuccess = True
                            self.formatDetailedResults("fix", self.rulesuccess,
                                           self.detailedresults)
                            self.logdispatch.log(LogPriority.INFO,
                                                 self.detailedresults)
                            return self.rulesuccess
                        self.editor1 = KVEditorStonix(self.statechglogger,
                                                      self.logger, "conf",
                                                      nfsfile, nfstemp, data1,
                                                      "present", "openeq")
                    elif self.ph.manager in ("yum", "zypper"):
                        self.editor1 = KVEditorStonix(self.statechglogger,
                                                      self.logger, "conf",
                                                      nfsfile, nfstemp, data1,
                                                      "present", "closedeq")
                    elif self.ph.manager == "apt-get":
                        self.editor1 = KVEditorStonix(self.statechglogger,
                                                      self.logger, "conf",
                                                      nfsfile, nfstemp, data1,
                                                      "present", "space")
                    if not self.editor1.report():
                        if not self.editor1.fix():
                            success = False
                            debug = "fix for editor1 failed"
                            self.logger.log(LogPriority.DEBUG, debug)
                        else:
                            if not self.editor1.commit():
                                success = False
                                debug = "commit for editor1 failed"
                                self.logger.log(LogPriority.DEBUG, debug)
                            else:
                                changed1 = True
                    if not checkPerms(nfsfile, [0, 0, 420], self.logger):
                        if not setPerms(nfsfile, [0, 0, 420], self.logger, self.statechglogger):
                            success = False
                            debug = "Unable to set permissions on " + nfsfile
                            self.logger.log(LogPriority.DEBUG, debug)
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    event = {"eventtype": "creation",
                             "filepath": nfsfile}
                    self.statechglogger.recordchgevent(myid, event)
                else:
                    success = False
                    debug = "Unable to create " + nfsfile + " file"
                    self.logger.log(LogPriority.DEBUG, debug)
            else:
                if self.editor1.fixables:
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    self.editor1.setEventID(myid)
                    if not self.editor1.fix():
                        success = False
                        debug = "editor1 fix failed"
                        self.logger.log(LogPriority.DEBUG, debug)
                    else:
                        if not self.editor1.commit():
                            success = False
                            debug = "editor1 commit failed"
                            self.logger.log(LogPriority.DEBUG, debug)
                        else:
                            changed1 = True
                if not checkPerms(nfsfile, [0, 0, 420], self.logger):
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    if not setPerms(nfsfile, [0, 0, 420], self.logger,
                                    self.statechglogger, myid):
                        debug = "Unable to set permissions on " + nfsfile
                        self.logger.log(LogPriority.DEBUG, debug)
            export = "/etc/exports"
            if not os.path.exists(export):
                if createFile(export, self.logger):
                    extemp = export + ".tmp"
                    data2 = {"all_squash": "",
                             "no_root_squash": "",
                             "insecure_locks": ""}
                    self.editor2 = KVEditorStonix(self.statechglogger,
                                                  self.logger, "conf", export,
                                                  extemp, data2, "notpresent",
                                                  "space")
                    if not self.editor2.report():
                        if not self.editor2.fix():
                            success = False
                            debug = "fix for editor2 failed"
                            self.logger.log(LogPriority.DEBUG, debug)
                        else:
                            if not self.editor2.commit():
                                success = False
                                debug = "commit for editor2 failed"
                                self.logger.log(LogPriority.DEBUG, debug)
                            else:
                                changed2 = True
                    if not checkPerms(export, [0, 0, 420], self.logger):
                        if not setPerms(export, [0, 0, 420], self.logger, self.statechglogger):
                            success = False
                            debug = "Unable to set permissions on " + export
                            self.logger.log(LogPriority.DEBUG, debug)
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    event = {"eventtype": "creation",
                             "filepath": export}
                    self.statechglogger.recordchgevent(myid, event)
            else:
                if installed:
                    extemp = export + ".tmp"
                    data2 = {"all_squash": "",
                             "no_root_squash": "",
                             "insecure_locks": ""}
                    self.editor2 = KVEditorStonix(self.statechglogger,
                                                  self.logger, "conf", export,
                                                  extemp, data2, "notpresent",
                                                  "space")
                    self.editor2.report()
                if self.editor2.removeables:
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    self.editor2.setEventID(myid)
                    if not self.editor2.fix():
                        success = False
                        debug = "editor2 fix failed"
                        self.logger.log(LogPriority.DEBUG, debug)
                    else:
                        if not self.editor2.commit():
                            success = False
                            debug = "editor2 commit failed"
                            self.logger.log(LogPriority.DEBUG, debug)
                        else:
                            changed2 = True
                if not checkPerms(export, [0, 0, 420], self.logger):
                    self.iditerator += 1
                    myid = iterate(self.iditerator, self.rulenumber)
                    if not setPerms(export, [0, 0, 420], self.logger,
                                    self.statechglogger, myid):
                        success = False
                        debug = "Unable to set permissions on " + export
                        self.logger.log(LogPriority.DEBUG, debug)
            if changed1 or changed2:
                if not self.sh.reloadservice(nfsservice, nfsservice):
                    debug = "Unable to restart nfs service"
                    self.logger.log(LogPriority.DEBUG, debug)
                    success = False
            return success
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.rulesuccess = False
            self.detailedresults += "\n" + traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        self.formatDetailedResults("fix", self.rulesuccess,
                                   self.detailedresults)
        self.logdispatch.log(LogPriority.INFO, self.detailedresults)
        return self.rulesuccess
