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
import json
import pathlib
import unittest

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.cache import NoCache

from test_esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_ispyb import UtilsISPyB

class Test(unittest.TestCase):

    def tes_updateProposalFromSMIS(self):
        UtilsISPyB.updateProposalFromSMIS(1, "mx415")
        
    def tes_createSession(self):
        # No longer used but test kept here for eventual future needs
        sessions = UtilsISPyB.createSession(1, "opcm01", "cm01")
        print(sessions)

    def test_uploadClassify2D(self):
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        urlBase = "http://linsvensson.esrf.fr:8090/ispyb/ispyb-ws/ispybWS"
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        testDataPath = pathlib.Path(__file__).parent / 'testdata'
        allParamsFile = str(testDataPath / "allParams.json")
        allParams = json.loads(open(allParamsFile).read())
        # pprint.pprint(allParams)
        inputParticlesStarFile = str(testDataPath / "input_particles.star")
        dictParticle = UtilsPath.getInputParticleDict(
            pathToInputParticlesStarFile=inputParticlesStarFile,
            allParams=allParams
        )
        testDataPath = pathlib.Path(__file__).parent / 'testdata'
        starFile = str(testDataPath / "relion_it025_model.star")
        dictModel = UtilsPath.parseRelionModelStarFile(starFile)
        UtilsISPyB.uploadClassify2D(
            client=client,
            proposal="mx415",
            particleSize=100,
            dictParticle=dictParticle,
            dictModel=dictModel,
            pyarchParticleFile=inputParticlesStarFile
        )




    def tes_addMovie(self):
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        # urlBase = UtilsISPyB.getUrlBase(2)
        urlBase = "http://linsvensson.esrf.fr:8090/ispyb/ispyb-ws/ispybWS"
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        technique = "EM"
        proposal = "mx415"
        proteinAcronym = "test1"
        sampleAcronym = "test"
        movieDirectory = "/data/visitor/mx415/cm01/20191029/RAW_DATA/mx2214/data"
        moviePath = "/data/visitor/mx415/cm01/20191029/RAW_DATA/mx2214/data/mx2214_00009.tif"
        movieNumber = "00005"
        amplitudeContrast = 0.1
        movieNumber=15739
        micrographPath=None
        thumbnailMicrographPath="/data/pyarch/2019/cm01/BLC11961/20191022/RAW_DATA/EPU_codvil4175_grid1_20191024_161204/Images-Disc1/GridSquare_24675647/Data/FoilHole_25709368_Data_24680228_24680229_20191026_0822.jpg"
        xmlMetaDataPath="/data/pyarch/2019/cm01/BLC11961/20191022/RAW_DATA/EPU_codvil4175_grid1_20191024_161204/Images-Disc1/GridSquare_24675647/Data/FoilHole_25709368_Data_24680228_24680229_20191026_0822.xml"
        voltage=300000
        sphericalAberration=2.7
        magnification=165000
        scannedPixelSize=0.827
        imagesCount=40
        dosePerImage=1.0
        positionX=-0.00030172659999999992
        positionY=0.00014890481600000026
        beamLineName="cm01"
        startTime="Sat Oct 26 08:37:32 CEST 2019"
        gridSquareSnapshotFullPath="/data/pyarch/2019/cm01/BLC11961/20191022/RAW_DATA/EPU_codvil4175_grid1_20191024_161204/Images-Disc1/GridSquare_24675647/GridSquare_20191025_082321.jpg"
        movieObject = client.service.addMovie(
            proposal=proposal,
            proteinAcronym=proteinAcronym,
            sampleAcronym=sampleAcronym,
            movieDirectory=movieDirectory,
            movieFullPath=moviePath,
            movieNumber=movieNumber,
            micrographFullPath=micrographPath,
            micrographSnapshotFullPath=thumbnailMicrographPath,
            xmlMetaDataFullPath=xmlMetaDataPath,
            voltage=voltage,
            sphericalAberration=sphericalAberration,
            amplitudeContrast=amplitudeContrast,
            magnification=magnification,
            scannedPixelSize=scannedPixelSize,
            imagesCount=imagesCount,
            dosePerImage=dosePerImage,
            positionX=positionX,
            positionY=positionY,
            beamlineName=beamLineName,
            gridSquareSnapshotFullPath=gridSquareSnapshotFullPath,
        )
        self.assertIsNotNone(movieObject)

    def test_addParticlePicker(self):
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        # urlBase = UtilsISPyB.getUrlBase(2)
        urlBase = "http://linsvensson.esrf.fr:8090/ispyb/ispyb-ws/ispybWS"
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        technique = "EM"
        proposal = "mx2112"
        firstMovieFullPath = "/data/visitor/mx2112/cm01/20210628/RAW_DATA/mx2261_BcsD_grid6_EPU/Images-Disc1/GridSquare_25590846/Data/FoilHole_25598436_Data_25597084_25597086_20210625_171939_fractions.tiff"
        pickingProgram = "Cryolo"
        particlePickingTemplate = "Template"
        particleDiameter = "160"
        numberOfParticles = "5034"
        particlePickerObject = client.service.addParticlePicker(
            proposal=proposal,
            firstMovieFullPath=firstMovieFullPath,
            pickingProgram=pickingProgram,
            particlePickingTemplate=particlePickingTemplate,
            particleDiameter=particleDiameter,
            numberOfParticles=numberOfParticles
        )
        self.assertIsNotNone(particlePickerObject)


    def tes_addParticleClassificationGroup(self):
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        # urlBase = UtilsISPyB.getUrlBase(2)
        urlBase = "http://linsvensson.esrf.fr:8090/ispyb/ispyb-ws/ispybWS"
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        particleClassificationGroupObject = client.service.addParticleClassificationGroup(
            particlePickerId="1",
            type="2D",
            batchNumber="1",
            numberOfParticlesPerBatch="2",
            numberOfClassesPerBatch="3",
            symmetry="4",
            classificationProgram="5"
        )
        self.assertIsNotNone(particleClassificationGroupObject)


    def test_addParticleClassification(self):
        httpAuthenticated = UtilsISPyB.getHttpAuthenticated()
        # urlBase = UtilsISPyB.getUrlBase(2)
        urlBase = "http://linsvensson.esrf.fr:8090/ispyb/ispyb-ws/ispybWS"
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        client = Client(url, transport=httpAuthenticated, cache=NoCache(), timeout=15)
        particleClassificationObject = client.service.addParticleClassification(
            particleClassificationGroupId="1",
            classNumber="2",
            classImageFullPath="3",
            particlesPerClass="4",
            classDistribution="5",
            rotationAccuracy="6",
            translationAccuracy="7",
            estimatedResolution="8",
            overallFourierCompleteness="9"
        )
        self.assertIsNotNone(particleClassificationObject)
