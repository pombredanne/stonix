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
This objects encapsulates the complexities of the networksetup command on OS X

@author: ekkehard j. koch
@change: 2015/05/07 ekkehard Original Implementation
@change: 2015/09/18 ekkehard add startup and casper options
'''
import re
import types
from .localize import PROXY
from .localize import PROXYCONFIGURATIONFILE
from .CommandHelper import CommandHelper


class networksetup():
    '''
    This objects encapsulates the complexities of the networksetup command
    on OS X
    
    @author: ekkehard j. koch
    '''

###############################################################################

    def __init__(self, logdispatcher):
        self.location = ""
        self.locationIsValidWiFiLocation = False
        self.locationInitialized = False
        self.ns = {}
        self.nsInitialized = False
        self.nso = {}
        self.nsInitialized = False
        self.resultReset()
        self.nsc = "/usr/sbin/networksetup"
        fullproxy = PROXY
        self.ps = fullproxy.split(":")[0] + ":" + fullproxy.split(":")[1]
        self.pp = fullproxy.split(":")[2]
        self.pf = PROXYCONFIGURATIONFILE
        self.dns = "128.165.4.4 128.165.4.33"
        self.searchdomain = "lanl.gov"
        self.logdispatch = logdispatcher
        self.ch = CommandHelper(self.logdispatch)
        self.initialized = False

###############################################################################

    def report(self):
        '''
        report is designed to implement the report portion of the stonix rule
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @return: boolean - true
        @note: None
        '''
        compliant = True
        self.initialize()
        if self.locationIsValidWiFiLocation:
            self.resultAppend("WiFi Network Setup for " + \
                              "services for location named " + \
                              str(self.location))
        else:
            self.resultAppend("Non-WiFi Network Setup for " + \
                              "services for location named " + \
                              str(self.location))
        for key in sorted(self.nso):
            network = self.nso[key]
            networkvalues = self.ns[network]
            networkname = networkvalues["name"]
            networktype = networkvalues["type"]
            networkenabled = networkvalues["enabled"]
            if networktype == "bluetooth" and networkenabled:
                compliant = False
                networkvalues["compliant"] = False
            elif networktype == "wi-fi" and networkenabled and \
            not self.locationIsValidWiFiLocation:
                compliant = False
                networkvalues["compliant"] = False
            else:
                networkvalues["compliant"] = True
            if networkvalues["compliant"]:
                messagestring = str(networkname) + " is compliant " + \
                ": " + str(networkvalues)
            else:
                messagestring = str(networkname) + " is NOT " + \
                "compliant : " + str(networkvalues)
            self.resultAppend(str(key) + " - " + messagestring)
        return compliant

###############################################################################

    def fix(self):
        '''
        fix is designed to implement the fix portion of the stonix rule
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @return: boolean - true
        @note: None
        '''
        fixed = True
        self.initialize()
        messagestring = "for location = " + str(self.location)
        for key in sorted(self.nso):
            network = self.nso[key]
            networkvalues = self.ns[network]
            networkname = networkvalues["name"]
            networktype = networkvalues["type"]
            networkenabled = networkvalues["enabled"]
            if networktype == "bluetooth" and networkenabled:
                fixedWorked = self.disableNetworkService(networkname)
                if fixedWorked:
                    networkvalues["compliant"] = True
                    messagestring = str(networkname) + " fixed " + \
                    ": " + str(networkvalues)
                else:
                    fixed = False
            elif networktype == "wi-fi" and networkenabled and \
            not self.locationIsValidWiFiLocation:
                fixedWorked = self.disableNetworkService(networkname)
                if fixedWorked:
                    networkvalues["compliant"] = True
                    messagestring = str(networkname) + " fixed " + \
                    ": " + str(networkvalues)
                else:
                    fixed = False
            elif networktype == "wi-fi" and not networkenabled and \
            self.locationIsValidWiFiLocation:
                fixedWorked = self.enableNetwork(networkname)
                if fixedWorked:
                    networkvalues["compliant"] = True
                    messagestring = str(networkname) + " fixed " + \
                    ": " + str(networkvalues)
                else:
                    fixed = False
            else:
                networkvalues["compliant"] = True
                messagestring = ""
            if not messagestring == "":
                self.resultAppend(messagestring)
        return fixed

###############################################################################

    def startup(self):
        '''
        startup is designed to implement the startup portion of the stonix rule
        
        @author: ekkehard j. koch
        '''
        disabled = True
        self.initialize()
        messagestring = "for location = " + str(self.location)
        for key in sorted(self.nso):
            network = self.nso[key]
            networkvalues = self.ns[network]
            networkname = networkvalues["name"]
            networktype = networkvalues["type"]
            networkenabled = networkvalues["enabled"]
            if networktype == "bluetooth" and networkenabled:
                fixedWorked = self.disableNetworkService(networkname)
                if fixedWorked:
                    networkvalues["compliant"] = True
                    messagestring = str(networkname) + " fixed " + \
                    ": " + str(networkvalues)
                else:
                    disabled = False
            elif networktype == "wi-fi" and networkenabled:
                fixedWorked = self.disableNetworkService(networkname)
                if fixedWorked:
                    networkvalues["compliant"] = True
                    messagestring = str(networkname) + " fixed " + \
                    ": " + str(networkvalues)
                else:
                    disabled = False
            else:
                networkvalues["compliant"] = True
                messagestring = ""
            if not messagestring == "":
                self.resultAppend(messagestring)
        return disabled

###############################################################################

    def getDetailedresults(self):
        '''
        get the detailed results text
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pLocationName:location name
        @return: string:detailedresults
        @note: None
        '''
        return self.detailedresults

###############################################################################

    def getLocation(self):
        '''
        get the location used by on the mac
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @return: boolean - true
        @note: None
        '''
        try:
            success = True
            command = [self.nsc, "-getcurrentlocation"]
            self.ch.executeCommand(command)
            for line in self.ch.getOutput():
                lineprocessed = line.strip()
                self.location = lineprocessed
                self.locationInitialized = True
            self.locationIsValidWiFiLocation = self.isValidLocationName(self.location)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            success = False
            raise
        return success
    
    def setAdvancedNetworkSetup(self, pNetworkName) :
        """
        Set proxies up for normal first configuration that has a network
        connection.
        
        @author: Roy Nielsen
        @param self:essential if you override this definition
        @param pNetworkName:name of the network to fix
        @return: boolean - true
        @note: None
        """
        success = True
# Set the DNS servers
        command = [self.nsc, "-setdnsservers", pNetworkName, self.dns]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# Set the Search Domain
        command = [self.nsc, "-setsearchdomains", pNetworkName, self.searchdomain]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# set up the auto proxy URL
        command = [self.nsc, "-setautoproxyurl", pNetworkName, self.pf]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# Set up the FTP proxy
        command = [self.nsc, "-setftpproxy", pNetworkName, self.ps, self.pp]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# Set up the HTTPS proxy
        command = [self.nsc, "-setsecurewebproxy", pNetworkName, self.ps, self.pp]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# Set up the web proxy
        command = [self.nsc, "-setwebproxy", pNetworkName, self.ps, self.pp]
        self.ch.executeCommand(command)
        if not self.ch.getError():
            success = False
# Get current proxy bypass domains and add lanl.gov
        command = [self.nsc, "-getproxybypassdomains", pNetworkName]
        self.ch.executeCommand(command)
        command = [self.nsc, "-setproxybypassdomains", pNetworkName]
        if self.ch.getError():
            for item in self.ch.getOutput() :
                if not re.match("^\s*$", item) :
                    command.append(item)
        if not "lanl.gov" in command:
            command.append("lanl.gov")
            self.ch.executeCommand(command)
            if not self.ch.getError():
                success = False

        return success

###############################################################################

    def initialize(self):
        '''
        initialize the object
        
        @author: ekkehard j. koch
        '''
        if not self.initialized:
            self.getLocation()
            self.updateCurrentNetworkConfigurationDictionary()
            self.initialized = True
        return self.initialized

###############################################################################

    def updateCurrentNetworkConfigurationDictionary(self):
        '''
        update the network configuration dictianry
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @return: boolean - true
        @note: None
        '''
        try:
            success = True
# issue networksetup -listallnetworkservices to get all network services
            command = [self.nsc, "-listnetworkserviceorder"]
            self.ch.executeCommand(command)
            order = -1
            newserviceonnexline = False
            newservice = False
            noinfo = False
            for line in self.ch.getOutput():
                if newserviceonnexline:
                    newservice = True
                    newserviceonnexline = False
                else:
                    newservice = False
                    newserviceonnexline = False
                if line == "An asterisk (*) denotes that a network service is disabled.\n":
                    infoOnThisLine = False
                    newserviceonnexline = True
                elif line == "\n":
                    infoOnThisLine = False
                    newserviceonnexline = True
                else:
                    infoOnThisLine = True
                lineprocessed = line.strip()
                if newservice and infoOnThisLine:
                    order = order + 1
# see if network is enabled
                    if lineprocessed[:3] == "(*)":
                        networkenabled = False
                    else:
                        networkenabled = True
                    linearray = lineprocessed.split()
                    linearray = linearray[1:]
                    servicename = ""
                    for item in linearray:
                        if servicename == "":
                            servicename = item
                        else:
                            servicename = servicename + " " + item
                    self.ns[servicename] = {"name": servicename,
                                            "enabled": networkenabled}
# determine network type
                elif infoOnThisLine:
                    lineprocessed = lineprocessed.strip("(")
                    lineprocessed = lineprocessed.strip(")")
                    linearray = lineprocessed.split(",")
                    for item in linearray:
                        lineprocessed = item.strip()
                        itemarray = lineprocessed.split(":")
                        if len(itemarray) > 1:
                            self.ns[servicename][itemarray[0].strip().lower()] = itemarray[1].strip()
                    hardwareport = self.ns[servicename]["hardware port"].lower()
                    splitline = hardwareport.split()
                    networktype = ""
                    for item in splitline:
                        if item.lower() == "ethernet":
                            networktype = item.lower()
                        elif item.lower() == "bluetooth":
                            networktype = item.lower()
                        elif item.lower() == "usb":
                            networktype = item.lower()
                        elif item.lower() == "wi-fi":
                            networktype = item.lower()
                        elif item.lower() == "firewire":
                            networktype = item.lower()
                        elif item.lower() == "thunderbolt":
                            networktype = item.lower()
                    if networktype == "":
                        networktype = "unknown"
# update dictionary entry for network
                    self.ns[servicename]["type"] = networktype
# create an ordered list to look up later
                    orderkey = str(order).zfill(4)
                    self.nso[orderkey] = servicename
                    self.updateNetworkConfigurationDictionaryEntry(servicename)
            self.nsInitialized = True
            self.nsoInitialized = True
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            success = False
            raise
        return success

###############################################################################

    def updateNetworkConfigurationDictionaryEntry(self, pKey):
        '''
        update a single network configuration dictionary entry 
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pkey:key for the dictinary entry
        @return: boolean - true
        @note: None
        '''
        try:
            success = True
            key = pKey
            entry = self.ns[key]
            if success:
                if entry == None:
                    success = False
            if success:
                command = [self.nsc, "-getmacaddress", key]
                self.ch.executeCommand(command)
                for line in self.ch.getOutput():
                    try:
                        macaddress = re.search("(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)",
                                               line.strip()).group(1)
                    except:
                        macaddress = ""
                    self.ns[key]["macaddress"] = macaddress
            if success:
                command = [self.nsc,
                           "-getnetworkserviceenabled", key]
                self.ch.executeCommand(command)
                for line in self.ch.getOutput():
                    lineprocessed = line.strip()
                    if lineprocessed == "Enabled":
                        self.ns[key]["enabled"] = True
                    else:
                        self.ns[key]["enabled"] = False
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            success = False
            raise
        return success

###############################################################################

    def isValidLocationName(self, pLocationName=""):
        '''
        determine if this is a valid wifi location
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pLocationName:location name
        @return: boolean - true
        @note: None
        '''
        success = False
        if pLocationName == "":
            locationName = self.location.lower()
        else:
            locationName = pLocationName.lower()
        if 'wi-fi' in locationName:
            success = True
        elif 'wifi' in locationName:
            success = True
        elif 'wireless' in locationName:
            success = True
        elif 'airport' in locationName:
            success = True
        elif 'off-site' in locationName:
            success = True
        elif 'offsite' in locationName:
            success = True
        else:
            success = False
        return success

###############################################################################

    def disableNetworkService(self, pNetworkName):
        '''
        disable network service
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pNetworkName:name of network
        @return: boolean - true
        @note: None
        '''
        try:
            success = True
            networkName = pNetworkName
            if networkName == "":
                success = False
            if success:
                command = [self.nsc,
                           "-setnetworkserviceenabled",
                           networkName, "off"]
                self.ch.executeCommand(command)
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            success = False
            raise
        return success

###############################################################################

    def enableNetwork(self, pNetworkName):
        '''
        enable network service
        
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pNetworkName:name of network
        @return: boolean - true
        @note: None
        '''
        try:
            success = True
            networkName = pNetworkName
            if networkName == "":
                success = False
            if success:
                command = [self.nsc,
                           "-setnetworkserviceenabled",
                           networkName, "on"]
                self.ch.executeCommand(command)
        except (KeyboardInterrupt, SystemExit):
            # User initiated exit
            raise
        except Exception:
            success = False
            raise
        return success

###############################################################################

    def resultAppend(self, pMessage=""):
        '''
        reset the current kveditor values to their defaults.
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @param pMessage:message to be appended
        @return: boolean - true
        @note: None
        '''
        datatype = type(pMessage)
        if datatype == types.StringType:
            if not (pMessage == ""):
                messagestring = pMessage
                if (self.detailedresults == ""):
                    self.detailedresults = messagestring
                else:
                    self.detailedresults = self.detailedresults + "\n" + \
                    messagestring
        elif datatype == types.ListType:
            if not (pMessage == []):
                for item in pMessage:
                    messagestring = item
                    if (self.detailedresults == ""):
                        self.detailedresults = messagestring
                    else:
                        self.detailedresults = self.detailedresults + "\n" + \
                        messagestring
        else:
            raise TypeError("pMessage with value" + str(pMessage) + \
                            "is of type " + str(datatype) + " not of " + \
                            "type " + str(types.StringType) + \
                            " or type " + str(types.ListType) + \
                            " as expected!")

###############################################################################

    def resultReset(self):
        '''
        reset the current kveditor values to their defaults.
        @author: ekkehard j. koch
        @param self:essential if you override this definition
        @return: boolean - true
        @note: kveditorName is essential
        '''
        self.detailedresults = ""
