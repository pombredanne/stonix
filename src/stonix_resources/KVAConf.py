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
Created on May 6, 2013

@author: dwalker
'''
from logdispatcher import LogPriority
from stonixutilityfunctions import writeFile
import traceback
import re

class KVAConf():
    '''This class checks files for correctness that consist of key:value pairs
    either in the form of closed equal separated (k=v), open separated (k = v),
    or space separated (k v).  To implement this class, the calling KVEditor 
    class must have already had the path set and the intent set.  The intent 
    should either be a value of 'present' or not 'present'.  The purpose of the
    intent is to determine whether the values you are setting are desired in 
    configuration file or not desired, where present = desired and notpresent
    = not desired.  If the same key appears more than once, this helper class
    will ensure only one value remains with the correct value in the end.
    The value associated with a key can either be a string or a list.  When
    the value is a list, this means that someone is passing in a key value set
    where the key is allowed to be the same over and over again such as a 
    blacklist file where you may see: 
    blacklist bluetooth
    blacklist rivafb
    blacklist hisax
    ...
    in which the dictionary would be in the form of: 
    {"blacklist:["bluetooth",
                 "rivafb",
                 "hisax"]}'''
###############################################################################
    def __init__(self, path, tmpPath, intent, configType, logger):
        self.fixables = {}
        self.removeables = {}
        self.contents = []
        self.logger = logger
        self.path = path
        self.tmpPath = tmpPath
        self.storeContents(self.path)
        self.configType = configType
        self.universal = "#The following lines were added by stonix\n"
        self.tempstring = ""
        self.intent = intent
        self.detailedresults = ""
###############################################################################
    def setPath(self, path):
        '''
        Private method to set the path of the configuration file
        @author: dwalker
        @param path: the path to file to be handled
        '''
        self.path = path
        self.storeContents(self.path)
###############################################################################
    def getPath(self):
        '''
        Private method to retrieve the path of the configuration file
        @author: dwalker
        @return: Bool
        '''
        return self.path
###############################################################################
    def setTmpPath(self, tmpPath):
        '''
        Private method to set the temporary path of the configuration file
        for writing before renaming to original file again
        @author: dwalker
        @param tmpPath: the path to the temporary file to be written to
        '''
        self.tmpPath = tmpPath
###############################################################################
    def getTmpPath(self):
        '''
        Private method to retrieve the temporary path of the configuration
        file to be written to before renaming to original file again
        @author: dwalker
        @return: Bool
        '''
        return self.tmpPath
###############################################################################
    def setIntent(self, intent):
        '''Private method to set the intent of self.data.  Should either be a
        value of "present" or "notpresent" to indicate whether key value pairs
        in self.data are desired or not desired in the configuration file
        respectively.  The point of this variable is to change from present 
        to notpresent when needed to set desirable and non desireable key 
        value pairs back and forth until update method is run. 
        @author: dwalker
        @param intent: present | notpresent
        '''
        self.intent = intent
###############################################################################
    def getIntent(self):
        '''
        Private method to retrieve the current intent
        @author: dwalker
        @return: present|notpresent
        '''
        return self.intent
###############################################################################
    def setConfigType(self, configType):
        self.configType = configType
        return True
###############################################################################
    def getConfigType(self):
        return self.configType
###############################################################################
    def validate(self, key, val):
        '''Private outer method to call submethod getOpenClosedValue() or
        getSpaceValue() depending on the value of self.configType.
        @author: dwalker
        @param key: key in a dictionary passed from calling class
        @param val: value part in dictionary passed from calling class
        @return: Bool
        '''
        if self.configType == 'openeq':
            return self.getOpenClosedValue(key, val)
        if self.configType == 'closedeq':
            return self.getOpenClosedValue(key, val)
        if self.configType == 'space':
            return self.getSpaceValue(key, val)
        else:
            return "invalid"
###############################################################################
    def getOpenClosedValue(self, key, value):
        '''
        Private inner method called by validate that populates self.fixables
        and/or self.removeables lists.  self.fixables list will be populated
        if configuration file has either the correct key but the wrong value
        or the key is not there at all.  A key that is commented out will be 
        considered not present. self.removeables list will be populated if 
        configuration file has keys that are not desired.  The value of these
        keys is irrelevant since the key shouldn't be there at all.  This 
        method specifcally handles files with an equal sign separating the key 
        and the val, both open and closed type
        @author: dwalker
        @param key: key in a dictionary passed from calling class
        @param val: value part in dictionary passed from calling class
        @return: Bool
        '''
        if self.contents:
            if self.intent == "present":  # self.data contains key val pairs we want in the file
                found = False
                for line in self.contents:
                    if re.match('^#', line) or re.match(r'^\s*$', line):  # ignore if comment or blank line
                        continue
                    elif re.search("=", line):  # examine line if there is an = sign
                        temp = line.split("=")  # split line into key val list [key, val]
                        if re.match("^" + key + "$", temp[0].strip()):  # it contains the current key we're looking for
                            if temp[1].strip() == value:  # and the value is correct
                                found = True  # however we continue to make sure the key doesn't appear later in the file and have the wrong value
                                continue
                            else:  # the value is wrong so we break out of the loop.  Unecessary to continue, it will be fixed in the update
                                found = False
                                break
                if found:  # return True or False value
                    return True
                else:
                    return False
            elif self.intent == "notpresent":  # self.data contains key val pairs we don't want in the file
                found = True
                for line in self.contents:
                    if re.match("^#", line) or re.match(r'^\s*$', line):  # ignore if comment or blank line
                        continue
                    elif re.search("=", line):  # examine line if there is an = sign
                        temp = line.split("=")  # split line into key val list [key, val]
                        if re.match("^" + key + "$", temp[0].strip()):  # it contains the current key we're looking for
                            found = True  # no need to check value, it's irrelevant
                            break
                return found
###############################################################################

    def getSpaceValue(self, key, value):
        '''
        Private inner method called by validate that populates self.fixables
        and/or self.removeables lists.  self.fixables list will be populated
        if configuration file has either the correct key but the wrong value
        or the key is not there at all.  A key that is commented out will be
        considered not present. self.removeables list will be populated if
        configuration file has keys that are not desired.This method
        specifcally handles files where a space separates key value pairs
        within the same line.
        @author: dwalker
        @param key: key in a dictionary passed from calling class
        @param val: value part in dictionary passed from calling class
        @return: Bool
        '''
        fixables = []
        removeables = []
        if self.contents:
            if self.intent == "present":  #self.data contains key val pairs we want in the file
                if isinstance(value, list):  # value can be a list in cases, see init pydoc
                    for item in value:
                        foundalready = False
                        for line in self.contents:
                            if re.match('^#', line) or re.match(r'^\s*$', line):  # ignore if comment or blank line
                                continue
                            elif re.search(key, line):  # we found the key, which in this case can be repeatable
                                temp = line.strip()  # strip off all trailing and leading whitespace
                                temp = re.sub("\s+", " ", temp)  # replace all whitespace with just one whitespace character
                                temp = temp.split()  # separate contents into list separated by spaces
                                if len(temp) > 0 and temp[0] == key:  # check to make sure key appears in beginning and has more than one item in the list
                                    try:
                                        if len(temp) > 2:  # this could indicate the file's format may be corrupted but that's not our issue
                                            continue
                                        elif temp[1] == item:  # value is correct
                                            foundalready = True
                                    except IndexError:
                                        self.detailedresults += "Index error\n"
                                        #maybe should continue instead of raising
                                        raise(self.detailedresults)
                        if not foundalready:
                            fixables.append(item)
                    if fixables:
                        return fixables
                    else:
                        return True
                else:  # value must be a string, normal case
                    found = False
                    for line in self.contents:
                        if re.match('^#', line) or re.match(r'^\s*$', line):  # ignore if comment or blank line
                            continue
                        elif re.search(key, line):  # the key is in this line
                            temp = line.strip()  # strip off all trailing and leading whitespace
                            temp = re.sub("\s+", " ", temp)  # replace all whitespace with just one whitespace character
                            temp = temp.split()  # separate contents into list separated by spaces
                            if len(temp) > 0 and temp[0] == key:  # check to make sure key appears in beginning and has more than one item in the list
                                try:
                                    if len(temp) > 2:
                                        continue  # this could indicate the file's format may be corrupted but that's not our issue
                                    elif temp[1] == value:  # the value is correct
                                        found = True  # however we continue to make sure the key doesn't appear later in the file and have the wrong value
                                        continue
                                    else:  # the value is wrong so we break out of the loop.  Unecessary to continue, it will be fixed in the update
                                        found = False
                                        break
                                except IndexError:
                                    found = False
                                    self.detailedresults += "Index error\n"
                                    break
                    return found
            elif self.intent == "notpresent":  # self.data contains key val pairs we don't want in the file
                if isinstance(value, list):  # value can be a list in cases, see init pydoc
                    for item in value:
                        foundalready = False
                        for line in self.contents:
                            if re.match('^#', line) or re.match(r'^\s*$', line):  # ignore if comment or blank line
                                continue
                            elif re.search(key, line):  # we found the key, which in this case can be repeatable
                                temp = line.strip()  # strip off all trailing and leading whitespace
                                temp = re.sub("\s+", " ", temp)  # replace all whitespace with just one whitespace character
                                temp = temp.split()  # separate contents into list separated by spaces
                                if len(temp) > 0 and temp[0] == key:  # check to make sure key appears in beginning and has more than one item in the list
                                    try:
                                        if len(temp) > 2:
                                            continue  # this could indicate the file's format may be corrupted but that's not our issue
                                        elif temp[1] == item:  # the value is correct
                                            foundalready = True
                                    except IndexError:
                                        self.detailedresults += "Index error\n"
                                        #maybe continue instead of raising
                                        raise(self.detailedresults)
                        if foundalready:
                            removeables.append(item)
                    if removeables:
                        return removeables
                    else:
                        return False
                else:  # value must be a string, normal case
                    found = False
                    for line in self.contents:
                        if re.match('^#', line) or re.match(r'^\s*$', line):  # ignore is comment or blank line
                            continue
                        elif re.match("^" + key, line):  # we found the key
                            temp = line.strip()  # strip off all trailing and leading whitespace
                            temp = re.sub("\s+", " ", temp)  # replace all whitespace with just one whitespace character
                            temp = temp.split()  # separate contents into list separated by spaces
                            if re.match("^" + key + "$", temp[0]):  # a more specific check of the key in case is shares a similar key name with another key up to a point
                                found = True
                                break
                    return found
###############################################################################

    def update(self, fixables, removeables):
        '''
        Private outer method to call submethod setOpenClosedValue() or
        setSpaceValue() depending on the value of self.configType.
        @author: dwalker
        @param fixables: a dictionary of key val pairs desired in file
        @param removeables: a dictionary of key val pairs not desired in file
        @return: Bool
        '''
        if self.configType == 'openeq':
            return self.setOpenClosedValue(fixables, removeables)
        if self.configType == 'closedeq':
            return self.setOpenClosedValue(fixables, removeables)
        if self.configType == 'space':
            return self.setSpaceValue(fixables, removeables)
        else:
            return "invalid"
###############################################################################

    def setOpenClosedValue(self, fixables, removeables):
        '''
        Private inner method called by update that makes a list to conform
        to desireable (fixables) key val pairs and undesireable (removeables)
        key val pairs in the config file while also keeping any other
        contents intact that aren't affected.  This method specifcally handles
        files with an equal sign separating the key and the val, both open
        and closed
        @author: dwalker
        @param fixables: a dictionary of key val paris desired in file
        @param removeables: a dictionary of key val paris not desired in file
        @return: Bool
        '''
        self.storeContents(self.path)  # re-read the contents of the desired file
        contents = self.contents
        if removeables:  # we have items that need to be removed from file
            for key in removeables:
                i = 0  # variable to keep our place in the list, will be used for removing items
                for line in contents:
                    if re.search("^#", line) or re.match("^\s*$", line):  # ignore if comment or blank line
                        i += 1
                    elif re.search("=", line.strip()):  # line contains an = sign
                        temp = line.split("=")
                        if re.match("^" + key + "$", temp[0].strip()):  # found the key
                            contents.pop(i)  # not concerned with the value because we don't want the key either way
                        i += 1
                    else:
                        i += 1
        if fixables:  # we have items that either had the wrong value or don't exist in the file
            for key in fixables:
                i = 0  # variable to keep our place in the list, will be used for removing items
                for line in contents:
                    if re.search("^#", line) or re.match("^\s*$", line):  # ignore if comment or blank line
                        i += 1
                    elif re.search("=", line.strip()):  # line contains an = sign
                        temp = line.split("=")
                        if re.match("^" + key + "$", temp[0].strip()):  # found the key
                            contents.pop(i)  # we pop it out but down below we add the correct line unlike above
                        i += 1
                    else:
                        i += 1
            self.contents = []
            for line in contents:  # contents should now have a list of items we are ok with having in the file but will still be missing the fixables
                self.contents.append(line)  # make self.contents contain the correct file contents before fixing
            self.contents.append("\n" + self.universal)  # add our universal line to show line(s) were added by stonix to self.contents
            for key in fixables:
                if self.configType == "openeq":  # construct the appropriate line and add to bottom of self.contents
                    temp = key + " = " + fixables[key] + "\n"
                    self.contents.append(temp)
                elif self.configType == "closedeq":
                    temp = key + "=" + fixables[key] + "\n"
                    self.contents.append(temp)
        return True
###############################################################################

    def setSpaceValue(self, fixables, removeables):
        '''
        Private inner method called by update that makes a list to conform
        to desireable (fixables) key val pairs and undesireable (removeables)
        key val pairs in the config file while also keeping any other
        contents intact that aren't affected.  This method specifcally handles
        files where a space separates key value pairs within the same line
        @author: dwalker
        @param fixables: a dictionary of key val paris desired in file
        @param removeables: a dictionary of key val paris not desired in file
        @return: Bool
        '''
#       re-read the contents of the desired file
        self.storeContents(self.path)
        contents = self.contents
        if removeables:  # we have items that need to be removed from file
            for key, val in removeables.iteritems():
                i = 0
#               we have a list where the key can repeat itself
                if isinstance(val, list):
                    for key2 in removeables[key]:
                        for line in contents:
                            if re.search("^#", line) or re.match("^\s*$",
                                                                 line):
                                i += 1
                            else:
                                temp = line.strip()
                                temp = re.sub("\s+", " ", temp)
                                temp = line.split()
                                if len(temp) > 2:
                                    i += 1
                                    continue
                                elif re.search("^" + key + "$", temp[0]):
                                    if re.search("^" + key2 + "$", temp[1]):
                                        contents.pop(i)
                                else:
                                    i += 1
                else:
                    for line in contents:
                        if re.search("^#", line) or re.match("^\s*$", line):
                            i += 1
                        elif re.search(key, line.strip()):
                            temp = line.strip().split(" ")
                            if re.match("^" + key + "$", temp[0].strip()):
                                contents.pop(i)
                        else:
                            i += 1
            self.contents = contents
            contents = self.contents
        if fixables:
            contents.append(self.universal)
            for key, val in fixables.iteritems():
                if isinstance(val, list):
                    continue
                    for key2 in fixables[key]:
                        contents.append(key + " " + key2 + "\n")
                else:
                    i = 0
                    for line in contents:
                        if re.search("^#", line) or re.match("^\s*$", line):
                            i += 1
                        elif re.search(key, line):
                            temp = line.strip()
                            temp = re.sub("\s+", " ", temp)
                            temp = line.split()
                            if len(temp) > 2:
                                i += 1
                                continue
                            #temp = line.strip().split()
                            elif re.match("^" + key + "$", temp[0].strip()):
                                contents.pop(i)
                            else:
                                i += 1
                        else:
                            i += 1
            for key, val in fixables.iteritems():
                if isinstance(val, list):
                    for key2 in fixables[key]:
                        contents.append(key + " " + key2 + "\n")
                else:
                    contents.append(key + " " + val + "\n")
        self.contents = contents
#             if listPresent:
#                 self.contents = contents
#                 return True
#             else:
#                 self.contents = []
#                 for line in contents:  # reconstruct the self.contents list to contain the most updated list
#                     self.contents.append(line)
#                 self.contents.append("\n" + self.universal)
#                 if fixables:  # if there are fixables, we need to then add those, removeables have already been taken care of above
#                     for key in fixables:
#                         temp = key + " " + fixables[key] + "\n"
#                         self.contents.append(temp)
#                 return True
        return True
###############################################################################

    def commit(self):
        '''
        Private method that actually writes the configuration file as desired
        including fixables and removing desireables.  This method is called
        in the calling class that instantiated the object after the update
        methods have been called.
        @author: dwalker
        @return: Bool
        '''
        for line in self.contents:
            self.tempstring += line
        success = writeFile(self.tmpPath, self.tempstring, self.logger)
        return success
###############################################################################

    def storeContents(self, path):
        '''
        Private method that reads in the self.path variable's contents and
        stores in private variable self.contents.
        @author: dwalker
        @param path: The path which contents need to be read
        '''
        try:
            f = open(path, 'r')
        except IOError:
            self.detailedresults = "KVAConf: unable to open the" \
                "specified file"
            self.detailedresults += traceback.format_exc()
            self.logger.log(LogPriority.DEBUG, self.detailedresults)
            return False
        self.contents = []
        for line in f:
            self.contents.append(line)
        f.close()
###############################################################################

    def getValue(self):
        '''
        Private method that puts any items that don't exist or have the wrong
        value (fixables) and any items that do exist but shouldn't
        (removeables) in string form for retrieving.  This method is more for
        debugging to make sure KVAConf is doing the right thing during when
        reporting (validate)
        @author: dwalker
        @return: str'''
        output = ""
        if self.fixables:
            output += "Keys that have incorrect values:\n" + \
                str(self.fixables) + "\n"
        if self.removeables:
            output += "Keys that need to be removed:\n" + \
                str(self.removeables) + "\n"
