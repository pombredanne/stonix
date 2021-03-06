"""
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
"""
import re
import socket
import httplib
import urllib
import urllib2

import SSLSecConnection
from stonixutilityfunctions import set_no_proxy
from logdispatcher import LogPriority

class ConnectivityInvalidURL(Exception):
    """
    Custom Exception    
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class Connectivity(object):
    """
    Check different methods of network connectivity
    
    @author: Roy Nielsen
    """
    def __init__(self, logger):
        """
        Constructor
        """
        self.logger = logger
        ##########################
        # Make it so this will only work on the yellow.
        set_no_proxy()

    ############################################################
        
    def is_site_socket_online(self, host):
        """ This function checks to see if a host name has a DNS entry by checking
            for socket info. If the website gets something in return, 
            we know it's available to DNS.
        """
        retval = False
        try:
            socket.setdefaulttimeout(5)
            socket.gethostbyname(host)
            retval = True
        except socket.gaierror, err:
            msg = "Can't connect to server, socket problem: " + str(err)
            self.logger.log(LogPriority.ERROR, msg)
        except socket.herror, exerr:
            msg = "Can't connect to server, socket problem: " + str(err)
            self.logger.log(LogPriority.ERROR, msg)
        except socket.timeout, err:
            msg = "Can't connect to server, socket problem: " + str(err)
            self.logger.log(LogPriority.ERROR, msg)
        except Exception, err:
            msg = "Can't connect to server, socket problem: " + str(err)
            self.logger.log(LogPriority.ERROR, msg)
        else:
            msg = "Socket connection available to: " + str(host)
            self.logger.log(LogPriority.ERROR, msg)
            
        return retval

    ############################################################

    def is_site_available(self, site="", path=""): #, path):
        """ This function retreives the status code of a website by requesting
            HEAD data from the host. This means that it only requests the headers.
            If the host cannot be reached or something else goes wrong, it returns
            False.
            
            This will only work if the self.set_no_proxy method is used before
            this method is called.
        """        
        retval = False

        try:
            page = site + path
            req = urllib2.Request(page, headers={'User-Agent' : "Magic Browser"}) 
            req.add_header('User-agent', 'Firefox/31.5.0')
            request = urllib2.urlopen(req, timeout=3)
            retval = True
        except urllib2.URLError, err:
            msg = "Error trying to get web page type: " + str(err)
            try:
                self.logger.log(LogPriority.ERROR, msg)
                if hasattr(err, 'code'):
                    msg = "code - " + str(err.code)
                    self.logger.log(LogPriority.ERROR, msg)
            except socket.gaierror, err:
                msg = "Can't connect to server, socket problem: " + str(err)
                self.logger.log(LogPriority.DEBUG, msg)
            except socket.herror, exerr:
                msg = "Can't connect to server, socket problem: " + str(err)
                self.logger.log(LogPriority.DEBUG, msg)
            except socket.timeout, err:
                msg = "Can't connect to server, socket problem: " + str(err)
                self.logger.log(LogPriority.DEBUG, msg)
            except Exception, err:
                msg = "General Exception: Can't connect to server: " + str(err)
                self.logger.log(LogPriority.DEBUG, msg)
        else:
            self.logger.log(LogPriority.DEBUG, "Got the right web page type.")
        
        return retval

    def isPageAvailable(self, url="", timeout=8):
        """
        Check if a specific webpage link is available, using httplib's 
        request('GET', url).  If a 200 is received in return, the connection
        to the page was successful.
        
        @parameter: url - valid http:// or https:// url
        @parameter: timeout - how fast to timeout the connection.
        """
        url = url.strip()
        self.logger.log(LogPriority.DEBUG, "URL: '" + str(url) + "'")
        self.logger.log(LogPriority.DEBUG, "timeout: " + str(timeout))
        
        success = False
        if isinstance(url, str):
            #####
            # Check for a valid URL
            if self.isUrlValid(url):
                self.logger.log(LogPriority.DEBUG, "URL is valid...")
                #####
                # Identify the different parts of the URL
                host, port, page = self.decomposeURL(url)
                self.logger.log(LogPriority.DEBUG, "host: " + str(host))
                self.logger.log(LogPriority.DEBUG, "port: " + str(port))
                self.logger.log(LogPriority.DEBUG, "page: " + str(page))
                              
                if host and port:
                    #####
                    # Create a different type of connection based on 
                    # http or https...
                    if re.match("^https://.+", url):
                        conn = httplib.HTTPSConnection(host=host, port=port, timeout=timeout, cert_file="", key_file="")
                    elif re.match("^http://.+", url):
                        conn = httplib.HTTPConnection(host, port, timeout)
                    #####
                    # Get the page, see if we get a return value of 200 
                    # (success)
                    try:                    
                        conn.request('GET', url)
                        response = conn.getresponse()
                    except socket.error:
                        self.logger.log(LogPriority.INFO, "No connection " + \
                                                           "to: " + str(url))
                    else:
                        self.logger.log(LogPriority.DEBUG, "Status: " + \
                                                           str(response.status))
                        if re.match("^200$", str(response.status)):
                            success = True

        return success

    def isUrlValid(self, url):
        """
        Check for a valid URL - 
        
        1 - cannot have multiple colons in the host portion of the url.
            one colon may separate the host and port, ie:
              proxy.example.com:8888
        2 - Only http and https are supported
        3 - the URL is a string
        """
        success = False
        
        if isinstance(url, str) and url:
            self.logger.log(LogPriority.DEBUG, "URL: '" + str(url) + "'")
            self.logger.log(LogPriority.DEBUG, "URL is a string and not empty...")
            if re.match("^http://.+", url) or re.match("^https://.+", url):
                self.logger.log(LogPriority.DEBUG, "Found valid protocol...")
                urlsplit = url.split("/")
                #####
                # Get the hostname, may be in the form of <host>:<port> or
                # ie: http://example.com:8080 would yield example.com:8080
                hostAndPort = urlsplit[2]
                self.logger.log(LogPriority.DEBUG, "urlsplit: " + str(urlsplit))
                if re.match(".+:.+", hostAndPort):
                    #####
                    # If there is a colon in the host field, get both
                    # the hostname and the port
                    self.logger.log(LogPriority.DEBUG, "hostAndPort:" + \
                                                        str(hostAndPort))
                    #####
                    # Get the host - check if there is a port indication in the URL, 
                    # ie. poxyout.example.com:8888 if so, get both.
                    hostList = hostAndPort.split(":")
                    self.logger.log(LogPriority.DEBUG, "hostList: " + str(hostlist))
                    ####
                    # Multiple colons is invalid, so raise an exception if two or 
                    # more are found.
                    if len(hostList) == 2 or not re.match(":", hostList):
                        success = True
                    else:
                        #####
                        # Problem parsing the URL passed in...
                        raise ConnectivityInvalidURL("Multiple colons in " + \
                                                     "hostname portion " + \
                                                     "of the URL...")
                elif not re.search(":", hostAndPort):
                    success = True
            else:
                self.logger.log(LogPriority.DEBUG, "Could NOT find valid " + \
                                                   "protocol...")                
        else:
            self.logger.log(LogPriority.DEBUG, "URL is not a string, or it " + \
                                               "is an empty string...")
        return success
    
    def decomposeURL(self, url=""):
        """
        Acquire the host, port and page of the URL and return them to the 
        caller.
        
        @parameter: url - a valid web URL, must be http:// or https://
        
        @returns: host - the host to which we want to connect.
        @returns: port - the port we want to connect to
        @returns: page - the rest of the string past the host:port section
                         of the URL.
        """
        host = ""
        port = 0
        page = ""
        if isinstance(url, basestring) and url:
            if re.match("^http://.+", url) or re.match("^https://.+", url):
                urlsplit = url.split("/")
                hostAndPort = urlsplit[2]
                if re.match(".+:.+", hostAndPort):
                    #####
                    # Get the host - check if there is a port indication in the URL, 
                    # ie. poxyout.example.com:8888 if so, get both.
                    hostList = hostAndPort.split(":")
                    self.logger.log(LogPriority.DEBUG, "hostList - " + str(hostList))
                    ####
                    # Multiple colons is invalid, so raise an exception if two or 
                    # more are found.
                    if len(hostList) < 2:
                        self.host = hostList[0]
                        self.port = hostList[1]
                elif not re.search(":", hostAndPort):
                    #####
                    # No port defined, use default ports
                    if re.match("^https://.+", url):
                        port = 443
                    elif re.match("^http://.+", url):
                        port = 80
                    host = hostAndPort
                        
                else:
                    raise ConnectivityInvalidURL("Multiple colons in " + \
                                                 " hostname portion " + \
                                                 "of the URL...")
                #####
                # Put together the "page" - or string after the 
                # host:port section of the URL
                try:
                    tmpstring = urlsplit[3:]
                    page = "/" + "/".join(tmpstring)
                except IndexError, err:
                    self.logger.log(LogPriority.DEBUG, "No page...")
                
        self.logger.log(LogPriority.DEBUG, "URL: " + str(url))
        self.logger.log(LogPriority.DEBUG, "host: " + str(host))
        self.logger.log(LogPriority.DEBUG, "port: " + str(port))
        self.logger.log(LogPriority.DEBUG, "page: " + str(page))

        return str(host), str(port), str(page)
