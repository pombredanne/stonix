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
Created on Sep 17, 2015
The Boot Security rule configures the system to run a job at system boot time
that handles turning off potential vulnerability points such as: wifi,
bluetooth, microphones, and cameras.

@author: dkennel
@change: 2015/10/07 eball Help text cleanup
'''

from __future__ import absolute_import
import traceback
import os
import re
import subprocess

from ..rule import Rule
from ..logdispatcher import LogPriority
from ..ServiceHelper import ServiceHelper


class BootSecurity(Rule):
    '''
    The Boot Security rule configures the system to run a job at system boot
    time that handles turning off potential vulnerability points such as: wifi,
    bluetooth, microphones, and cameras.
    '''

    def __init__(self, config, environ, logger, statechglogger):
        '''
        Constructor
        '''
        Rule.__init__(self, config, environ, logger, statechglogger)
        self.rulenumber = 18
        self.rulename = 'BootSecurity'
        self.formatDetailedResults("initialize")
        self.mandatory = True
        self.helptext = '''The BootSecurity rule configures the system to run \
a job at system boot time that ensures that WiFi and Bluetooth are turned off, \
and that microphone inputs are muted. This helps ensure that the system is in \
a secure state at initial startup.'''
        self.rootrequired = True
        self.guidance = []
        self.applicable = {'type': 'white',
                           'family': ['linux'],
                           'os': {'Mac OS X': ['10.9', 'r', '10.11.10']}}
        self.servicehelper = ServiceHelper(environ, logger)
        self.type = 'rclocal'
        self.rclocalpath = '/etc/rc.local'
        if os.path.islink(self.rclocalpath):
                paths = ['/etc/rc.d/rc.local', '/etc/init.d/rc.local']
                for rcpath in paths:
                    if os.path.isfile(rcpath):
                        self.rclocalpath = rcpath
        self.logdispatch.log(LogPriority.DEBUG,
                             'Using rc.local file ' + self.rclocalpath)
        if os.path.exists('/bin/systemctl'):
            self.type = 'systemd'
        elif os.path.exists('/sbin/launchd'):
            self.type = 'mac'
        self.plistpath = '/Library/LaunchDaemons/stonixBootSecurity.plist'

        self.plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>gov.lanl.stonix.bootsecurity</string>
    <key>Program</key>
    <string>
        <string>/Applications/stonix4mac.app/Contents/Resources/stonix.app/Contents/MacOS/stonix_resources/stonixBootSecurityMac</string>
    </string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''

        datatype = 'bool'
        key = 'bootsecurity'
        instructions = '''To disable this rule set the value of BOOTSECURITY \
to False.'''
        default = True
        self.bootci = self.initCi(datatype, key, instructions, default)

    def auditsystemd(self):
        try:
            servicelist = self.servicehelper.listservices()
            if 'stonixBootSecurity.service' in servicelist:
                return True
            else:
                return False
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.auditsystemd: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def auditrclocal(self):
        try:
            compliant = False
            rhandle = open(self.rclocalpath, 'r')
            rclocalcontents = rhandle.readlines()
            rhandle.close()
            for line in rclocalcontents:
                self.logdispatch.log(LogPriority.DEBUG,
                                     'Processing rc.local line ' + line)
                if re.search('^#', line):
                    continue
                elif re.search('stonixBootSecurity', line):
                    compliant = True
            return compliant
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.auditrclocal: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def auditmac(self):
        try:
            if os.path.exists(self.plistpath):
                return True
            else:
                return False
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.auditmac: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def report(self):
        if self.type == 'mac':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Checking for Mac plist')
            self.compliant = self.auditmac()
            if not self.compliant:
                self.detailedresults = 'Plist for stonixBootSecurity Launch Daemon not found.'
        elif self.type == 'systemd':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Checking for systemd service')
            self.compliant = self.auditsystemd()
            if not self.compliant:
                self.detailedresults = 'Service for stonixBootSecurity not active.'
        elif self.type == 'rclocal':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Checking rc.local')
            self.compliant = self.auditrclocal()
            if not self.compliant:
                self.detailedresults = 'stonixBootSecurity-Linux not scheduled in rc.local.'
        else:
            self.detailedresults = 'ERROR: Report could not determine where boot job should be scheduled!'
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
        if self.compliant:
            self.detailedresults = 'stonixBootSecurity correctly scheduled for execution at boot.'
            self.currstate = 'configured'

    def setsystemd(self):
        try:
            fmode = 436  # Integer representation of 664
            unitFileContents = """[Unit]
Description=Stonix Boot Security
After=network.target

[Service]
ExecStart=/usr/bin/stonix_resources/stonixBootSecurityLinux.py

[Install]
WantedBy=multi-user.target
"""
            unitFilePath = '/etc/systemd/system/stonixBootSecurity.service'
            whandle = open(unitFilePath, 'w')
            whandle.write(unitFileContents)
            whandle.close()
            os.chown(unitFilePath, 0, 0)
            os.chmod(unitFilePath, fmode)
            reloadcmd = '/bin/systemctl daemon-reload'
            try:
                proc = subprocess.Popen(reloadcmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=True)
            except Exception:
                pass
            self.servicehelper.enableservice('stonixBootSecurity')
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.setsystemd: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.rulesuccess = False
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def setrclocal(self):
        try:
            tempfile = self.rclocalpath + '.stonixtmp'
            command = '/usr/bin/stonix_resources/stonixBootSecurityLinux.py'
            fhandle = open(self.rclocalpath, 'r')
            rcdata = fhandle.readlines()
            fhandle.close()
            newdata = []
            inserted = False
            for line in rcdata:
                self.logdispatch.log(LogPriority.DEBUG,
                                     'Processing rc.local line ' + line)
                if re.search('^#', line):
                    newdata.append(line)
                elif re.search('^\n', line) and not inserted:
                    newdata.append(command)
                    newdata.append(line)
                    inserted = True
                elif re.search('exit 0', line) and not inserted:
                    newdata.append(command)
                    newdata.append(line)
                    inserted = True
                else:
                    newdata.append(line)
            if not inserted:
                self.logdispatch.log(LogPriority.DEBUG,
                                     'Insert not made, appending')
                newdata.append(command)
            whandle = open(tempfile, 'w')
            for line in newdata:
                whandle.write(line)
            whandle.close()
            mytype1 = 'conf'
            mystart1 = 'not configured'
            myend1 = 'configured'
            myid1 = '0018001'
            self.statechglogger.recordfilechange(self.rclocalpath, tempfile,
                                                 myid1)
            event1 = {'eventtype': mytype1,
                      'startstate': mystart1,
                      'endstate': myend1,
                      'myfile': self.rclocalpath}
            self.statechglogger.recordchgevent(myid1, event1)
            os.rename(tempfile, self.rclocalpath)
            os.chown(self.rclocalpath, 0, 0)
            os.chmod(self.rclocalpath, 493)  # Integer of 0755
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.setrclocal: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.rulesuccess = False
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def setmac(self):
        try:
            jobpath = '/Library/LaunchDaemons/stonixBootSecurity.plist'
            whandle = open(jobpath, 'w')
            whandle.write(self.plist)
            whandle.close()
            os.chown(jobpath, 0, 0)
            os.chmod(jobpath, 420)  # Integer of 0644
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            self.detailedresults = 'BootSecurity.setmac: '
            self.detailedresults = self.detailedresults + \
            traceback.format_exc()
            self.rulesuccess = False
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)

    def fix(self):
        if not self.bootci.getcurrvalue():
            return True
        if self.type == 'mac':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Creating Mac plist')
            self.setmac()
        elif self.type == 'systemd':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Creating systemd service')
            self.setsystemd()
        elif self.type == 'rclocal':
            self.logdispatch.log(LogPriority.DEBUG,
                                 'Creating rc.local entry')
            self.setrclocal()
        else:
            self.detailedresults = 'ERROR: Fix could not determine where boot job should be scheduled!'
            self.logdispatch.log(LogPriority.ERROR, self.detailedresults)
            self.rulesuccess = False
        self.rulesuccess = True
        self.currstate = 'configured'

    def undo(self):
        if self.type == 'mac':
            os.remove('/Library/LaunchDaemons/stonixBootSecurity.plist')
        elif self.type == 'systemd':
            os.remove('/etc/systemd/system/stonixBootSecurity.service')
        elif self.type == 'rclocal':
            try:
                event = self.statechglogger.getchgevent('0018001')
                if event['startstate'] != event['endstate']:
                    self.statechglogger.revertfilechanges(self.rclocalpath,
                                                          '0018001')
            except(IndexError, KeyError):
                self.logdispatch.log(LogPriority.DEBUG,
                                     ['BootSecurity.undo',
                                      "EventID 0018001 not found"])
        self.detailedresults = 'The Boot Security scripts have been removed.'
        self.currstate = 'notconfigured'