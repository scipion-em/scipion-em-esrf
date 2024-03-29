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
import datetime
import configparser

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.cache import NoCache


class UtilsISPyB(object):
    @staticmethod
    def getHttpAuthenticated():
        username = os.environ.get("ISPyB_user", None)
        password = os.environ.get("ISPyB_pass", None)
        if username is None or password is None:
            raise RuntimeError(
                "Missing ISPyB user name and / or password! Please ser ISPyB_user and ISPyB_pass."
            )
        return HttpAuthenticated(username=username, password=password)

    @staticmethod
    def getUrlBase(dbNumber):
        config = configparser.ConfigParser()
        config.read("/opt/pxsoft/scipion/config/esrf.properties")
        # URL
        urlBase = str(config.get("UrlBase", "url_{0}".format(dbNumber)))
        return urlBase

    @staticmethod
    def splitProposalInCodeAndNumber(proposal):
        code = None
        number = None
        if proposal is not None:
            listCodes = [
                "fx",
                "mxihr",
                "mx",
                "bx",
                "ix",
                "in",
                "im",
                "ihls",
                "ih-ls",
                "ihmx",
                "ih-mx",
                "ihsc",
                "ih-sc",
                "blc",
                "bm161",
                "sc",
                "tc",
                "opcm",
                "opid",
            ]
            proposalLowerCase = proposal.lower()
            for tmpCode in listCodes:
                if proposalLowerCase.startswith(tmpCode):
                    code = tmpCode
                    number = proposalLowerCase.split(code)[1]
                    # Check that we have an integer number
                    if not number.isdigit():
                        code = None
                        number = None
                    # "Fix" ih-ls, ih-mc and ih-sc proposals
                    elif code == "ihls":
                        code = "ih-ls"
                    elif code == "ihmx":
                        code = "ih-mx"
                    elif code == "ihsc":
                        code = "ih-sc"
        return code, number

    @staticmethod
    def getClient(url):
        # Authentication
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        return client

    @staticmethod
    def updateProposalFromSMIS(dbNumber, proposal):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "UpdateFromSMISWebService?wsdl")
        client = UtilsISPyB.getClient(url)
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        response = client.service.updateProposalFromSMIS(code, number)
        print(response)

    @staticmethod
    def findSessions(dbNumber, proposal, beamline):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForCollectionWebService?wsdl")
        # Authentication
        client = UtilsISPyB.getClient(url)
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        # print(code, number, beamline)
        sessions = client.service.findSessionsByProposalAndBeamLine(
            code, number, beamline
        )
        return sessions

    @staticmethod
    def findProposal(dbNumber, proposal):
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForShippingWebService?wsdl")
        # Authentication
        client = UtilsISPyB.getClient(url)
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal.lower())
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
            newSessionDict["proposalId"] = proposalDict["proposalId"]
            newSessionDict["startDate"] = startTime
            newSessionDict["endDate"] = endTime
            newSessionDict["beamlineName"] = beamline.upper()
            newSessionDict["scheduled"] = 0
            newSessionDict["nbShifts"] = 3
            newSessionDict["comments"] = "Session created by Scipion"

            urlBase = UtilsISPyB.getUrlBase(dbNumber)
            url = os.path.join(urlBase, "ToolsForCollectionWebService?wsdl")
            print(url)
            # Authentication
            client = UtilsISPyB.getClient(url)
            code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
            print(code, number, beamline)
            sessions = client.service.storeOrUpdateSession(newSessionDict)
        return sessions

    @staticmethod
    def getProposal(movieFilePath):
        proposal = None
        list_directory = movieFilePath.split(os.sep)
        # First check: directory must start with "data":
        if list_directory[1] == "data":
            proposal_from_directory = None
            if list_directory[2] == "visitor":
                proposal_from_directory = list_directory[3]
            else:
                proposal_from_directory = list_directory[4]
            proposal_code, proposal_number = UtilsISPyB.splitProposalInCodeAndNumber(
                proposal_from_directory
            )
            if proposal_code is not None:
                proposal = "{0}{1}".format(proposal_code, proposal_number)
        return proposal

    @staticmethod
    def uploadClassify2D(
        client, proposal, particleSize, dictParticle, dictModel, pyarchParticleFile
    ):
        particlePickerObject = client.service.addParticlePicker(
            proposal=proposal,
            firstMovieFullPath=dictParticle["firstMovieFullPath"],
            pickingProgram="Cryolo CPU",
            particlePickingTemplate="",
            particleDiameter=str(particleSize),
            numberOfParticles=dictParticle["numberOfParticles"],
            fullPathToParticleFile=pyarchParticleFile,
        )
        if particlePickerObject is not None:
            particlePickerId = particlePickerObject.particlePickerId
        else:
            particlePickerId = None
            pass
            # raise RuntimeError("ISPyB: particlePickerObject is None!")

        # Parse the "relion_it025_model.star" file
        if particlePickerId is not None:
            particleClassificationGroupObject = (
                client.service.addParticleClassificationGroup(
                    particlePickerId=particlePickerId,
                    type="2D",
                    batchNumber="0",
                    numberOfParticlesPerBatch="0",
                    numberOfClassesPerBatch="0",
                    symmetry="",
                    classificationProgram="Relion 2D classification",
                )
            )

            if particleClassificationGroupObject is not None:
                particleClassificationGroupId = (
                    particleClassificationGroupObject.particleClassificationGroupId
                )
            else:
                particleClassificationGroupId = None
                pass
                # raise RuntimeError("ISPyB: particleClassificationGroupId is None!")
            if particleClassificationGroupId is not None:
                for classModel in dictModel["classes"]:
                    particleClassificationObject = (  # noqa F841
                        client.service.addParticleClassification(
                            particleClassificationGroupId=particleClassificationGroupId,
                            classNumber=classModel["index"],
                            classImageFullPath=classModel["classImageFullPath"],
                            classDistribution=str(classModel["classDistribution"]),
                            rotationAccuracy=str(classModel["accuracyRotations"]),
                            translationAccuracy=str(
                                classModel["accuracyTranslationsAngst"]
                            ),
                            estimatedResolution=str(classModel["estimatedResolution"]),
                            overallFourierCompleteness=str(
                                classModel["overallFourierCompleteness"]
                            ),
                        )
                    )
