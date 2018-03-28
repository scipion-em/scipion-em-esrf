# coding: utf-8
# **************************************************************************
# *
# * Author:     Olof Svensson (svensson@esrf.fr) [1]
# *
# * [1] European Synchrotron Radiation Facility
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************


import os
import re
import sys
import glob
import math
import time
import socket
import shutil
import pprint
import datetime
import traceback
import ConfigParser
import xml.etree.ElementTree

sys.path.insert(0, "/opt/pxsoft/EDNA/vMX/edna/libraries/suds-0.4")

from suds.client import Client
from suds.transport.http import HttpAuthenticated

class UtilsISPyB(object):



    @staticmethod
    def getHttpAuthenticated():
        credentialsConfig = ConfigParser.ConfigParser()
        credentialsConfig.read(os.path.join(os.path.dirname(__file__), 'credentials.properties'))
        username = str(credentialsConfig.get('Credential', 'user'))
        password = str(credentialsConfig.get('Credential', 'password'))
        return HttpAuthenticated(username = username, password = password )
    
    @staticmethod
    def getUrlBase(dbNumber):
        config = ConfigParser.ConfigParser()
        # Configuration files
        config.read(os.path.join(os.path.dirname(__file__), 'ispyb.properties'))    
        # URL
        urlBase = str(config.get('UrlBase', 'url_{0}'.format(dbNumber)))
        return urlBase
    
    @staticmethod
    def splitProposalInCodeAndNumber(proposal):
        code = None
        number = None
        if proposal.startswith("mx"):
            code = "mx"
            number = proposal.split("mx")[1]
        elif proposal.startswith("blc"):
            code = "blc"
            number = proposal.split("blc")[1]
        return code, number
    
    @staticmethod
    def getClient(dbNumber):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl") 
        # Authentication
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        client = Client( url, transport = httpAuthenticated, cache = None, timeout = 15 )
        return client  

    @staticmethod
    def updateProposalFromSMIS(dbNumber, proposal):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "UpdateFromSMISWebService?wsdl")
        # Authentication
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        client = Client( url, transport = httpAuthenticated, cache = None, timeout = 15 )
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        response = client.service.updateProposalFromSMIS(code, number)
        print(response)
 
    @staticmethod
    def findSessions(dbNumber, proposal, beamline):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForCollectionWebService?wsdl")
        # Authentication
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        client = Client( url, transport = httpAuthenticated, cache = None, timeout = 15 )
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        # print(code, number, beamline)
        sessions = client.service.findSessionsByProposalAndBeamLine(code, number, beamline)
        return sessions      
    
    @staticmethod
    def findProposal(dbNumber, proposal):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForShippingWebService?wsdl")
        # Authentication
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        client = Client( url, transport = httpAuthenticated, cache = None, timeout = 15 )
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        # print(code, number)
        proposal = client.service.findProposal(code, number)
        return proposal
    
    
    @staticmethod
    def createSession(dbNumber, proposal, beamline):
        sessions = []
        proposalDict = UtilsISPyB.findProposal(dbNumber, proposal)
        if "proposalId" in proposalDict:
            currentTime = datetime.datetime.now()
            startTime = datetime.datetime.combine(currentTime, datetime.time(0, 0))
            tomorrow = startTime + datetime.timedelta(days=1)
            endTime = datetime.datetime.combine(tomorrow, datetime.time(7, 59, 59))
    
            # Create a session
            newSessionDict = {}
            newSessionDict['proposalId'] = proposalDict["proposalId"]
            newSessionDict['startDate'] = startTime
            newSessionDict['endDate'] = endTime
            newSessionDict['beamlineName'] = beamline.upper()
            newSessionDict['scheduled'] = 0
            newSessionDict['nbShifts'] = 3
            newSessionDict['comments'] = "Session created by Scipion"
            
            urlBase = UtilsISPyB.getUrlBase(dbNumber)
            url = os.path.join(urlBase, "ToolsForCollectionWebService?wsdl")
            print(url)
            # Authentication
            httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
            client = Client( url, transport = httpAuthenticated, cache = None, timeout = 15 )
            code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
            print(code, number, beamline)
            sessions = client.service.storeOrUpdateSession(newSessionDict)
        return sessions


    @staticmethod
    def getProposal(movieFilePath):
        proposal = None
        listDirectory = movieFilePath.split(os.sep)
        # First check: directory must start with "data":
        if listDirectory[1] == "data":
            # Check if ihls2975 - temporary fix
            if "IH-LS-2975" in movieFilePath:
                proposal = "ihls2975"
            # If not check if second level is "visitor":
            elif listDirectory[2] == "visitor":
                proposal = listDirectory[3]
            elif listDirectory[3] == "inhouse":
                proposal = listDirectory[4]
        return proposal
        
    
    
    
 