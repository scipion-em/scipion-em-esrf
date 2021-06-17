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

# This code is based on the "protocol_monitor_ispyb.py" written by
# J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es) [1] and
# Kevin Savage (kevin.savage@diamond.ac.uk) [2]
# [1] Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# [2] Diamond Light Source, Ltd

import os
import sys
import json
import time
import pprint
import shutil
import traceback
import collections

import pyworkflow.protocol.params as params

from pyworkflow import VERSION_1_1
from pyworkflow.protocol import getUpdatedProtocol
from emfacilities.protocols import ProtMonitor, Monitor, PrintNotifier
from pwem.protocols import ProtImportMovies, ProtAlignMovies, ProtCTFMicrographs
from relion.protocols import ProtRelionClassify2D
# from xmipp3.protocols import XmippProtMovieMaxShift
from motioncorr.protocols import ProtMotionCorr
from esrf.utils.esrf_utils_ispyb import UtilsISPyB
from esrf.utils.esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_icat import UtilsIcat


class ProtMonitorISPyB_ESRF(ProtMonitor):
    """ 
    Monitor to communicated with ISPyB system at ESRF.
    """
    _label = 'monitor to ISPyB at the ESRF'
    _lastUpdateVersion = VERSION_1_1

    def __init__(self, **kwargs):
        ProtMonitor.__init__(self, **kwargs)

    def _defineParams(self, form):
        ProtMonitor._defineParams(self, form)

        section1 = form.addSection(label='Names')

        section1.addParam(
            'proposal', params.StringParam,
            default="unknown",
            label="Proposal", important=True,
            help="Proposal")

        section1.addParam(
            'sampleAcronym', params.StringParam,
            default="unknown",
            label="Sample acronym", important=True,
            help="Name of the sample acronym")

        section1.addParam(
            'proteinAcronym', params.StringParam,
            default="unknown",
            label="Protein acronym", important=True,
            help="Name of the protein acronym")

        section2 = form.addSection(label='Experiment')

        section2.addParam(
            'dataType', params.EnumParam,
            choices=["EPU", "EPU_TIFF", "SERIALEM"],
            default = 0,
            label="Data type",
            help="Select which type of data that has been collected.")

        section2.addParam(
            'voltage', params.IntParam,
            default=300000,
            label="Voltage", important=True,
            help="Voltage in [V]")

        section2.addParam(
            'magnification', params.IntParam,
            default=100000,
            label="Nominal magnification", important=True,
            help="Nominal magnification")

        section2.addParam(
            'imagesCount', params.IntParam,
            default=40,
            label="Images count", important=True,
            help="Number of images per movie")

        section2.addParam(
            'alignFrame0', params.IntParam,
            default=1,
            label="Align Frame 0",
            help="Starting frame for motion correction")

        section2.addParam(
            'alignFrameN', params.IntParam,
            default=-1,
            label="Align Frame N",
            help="End frame for motion correction (-1 = all frames)")

        section2.addParam(
            'gainFilePath', params.StringParam,
            default="",
            label="Gain file",
            help="Gain file path for Motioncor 2")

        section2.addParam(
            'defectMapPath', params.StringParam,
            default="",
            label="Defect map file",
            help="Defect map path for Motioncor 2")

        section3 = form.addSection(label='ISPyB')

        section3.addParam(
            'db', params.EnumParam,
            choices=["production", "valid", "linsvensson"],
            default = 0,
            label="Database",
            help="Select which ISPyB database you want to use.")

        section3.addParam(
            'allParamsJsonFile', params.StringParam,
            default="",
            label="All parameters json file",
            help="Json file containing all parameters from processing.")

    #--------------------------- INSERT steps functions ------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('monitorStep')

    #--------------------------- STEPS functions -------------------------------
    def monitorStep(self):
        dbNumber = self.db.get()
        urlBase = UtilsISPyB.getUrlBase(dbNumber)
        url = os.path.join(urlBase, "ToolsForEMWebService?wsdl")
        self.info("ISPyB URL: {0}".format(url))
        self.client = UtilsISPyB.getClient(url)

        # # Update proposal
        # UtilsISPyB.updateProposalFromSMIS(dbNumber, self.proposal.get())
        #
        monitor = MonitorISPyB_ESRF(self, workingDir=self._getPath(),
                                        samplingInterval=30, # 30 seconds                                        # samplingInterval=self.samplingInterval.get(),
                                        monitorTime=4*24*60) # 4*24 H max monitor time

        monitor.addNotifier(PrintNotifier())
        monitor.loop()


class MonitorISPyB_ESRF(Monitor):
    """ This will will be monitoring a CTF estimation protocol.
    It will internally handle a database to store produced
    CTF values.
    """
    def __init__(self, protocol, **kwargs):
        Monitor.__init__(self, **kwargs)
        self.protocol = protocol
        self.allIds = collections.OrderedDict()
        self.numberOfFrames = None
        self.imageGenerator = None
        self.project = self.protocol.getProject()
        self.client = protocol.client
        self.proposal = protocol.proposal.get()
        self.proteinAcronym = protocol.proteinAcronym.get()
        self.sampleAcronym = protocol.sampleAcronym.get()
        self.movieDirectory = None
        self.currentDir = os.getcwd()
        self.currentGridSquare = None
        self.currentGridSquareLastMovieTime = None
        self.beamlineName = "cm01"
        self.dataType = protocol.dataType.get()
        self.voltage = protocol.voltage.get()
        self.magnification = protocol.magnification.get()
        self.imagesCount = protocol.imagesCount.get()
        self.alignFrame0 = protocol.alignFrame0.get()
        self.alignFrameN = protocol.alignFrameN.get()
        self.gainFilePath = protocol.gainFilePath.get()
        self.defectMapPath = protocol.defectMapPath.get()
        self.positionX = None
        self.positionY = None
        self.collectionDate = None
        self.collectionTime = None
        if hasattr(protocol, "allParamsJsonFile"):
            self.allParamsJsonFile = protocol.allParamsJsonFile.get()
            if os.path.exists(self.allParamsJsonFile):
                try:
                    dictAllParams = json.loads(open(self.allParamsJsonFile).read())
                    self.allParams = collections.OrderedDict(dictAllParams)
                except:
                    self.allParams = collections.OrderedDict()
            else:
                self.allParams = collections.OrderedDict()
        else:
            self.allParamsJsonFile = None
            self.allParams = collections.OrderedDict()

    def step(self):
        self.info("MonitorISPyB: start step ------------------------")
        self.info("Number of movies in all params: {0}".format(len(self.allParams)))

        # Check if we should archive gain an defect maps
        self.archiveGainAndDefectMap()

        if self.proposal == "None":
            self.info("WARNING! Proposal is 'None', no data uploaded to ISPyB")
            finished = True
        else:
            prots = [getUpdatedProtocol(p) for p in self.protocol.getInputProtocols()]

            g = self.project.getGraphFromRuns(prots)

            nodes = g.getRoot().iterChildsBreadth()

            isActiveImportMovies = True
            isActiveAlignMovies = True
            isActiveCTFMicrographs = True
            isActiveClassify2D = True

            for n in nodes:
                prot = n.run
                #self.info("Protocol name: {0}".format(prot.getRunName()))

                if isinstance(prot, ProtImportMovies):
                    self.uploadImportMovies(prot)
                    isActiveImportMovies = prot.isActive()
                # elif isinstance(prot, XmippProtMovieMaxShift) and hasattr(prot, 'outputMicrographs'):
                elif isinstance(prot, ProtMotionCorr) and hasattr(prot, 'outputMicrographs'):
                    self.uploadAlignMovies(prot)
                    isActiveAlignMovies = prot.isActive()
                elif isinstance(prot, ProtCTFMicrographs) and hasattr(prot, 'outputCTF'):
                    self.uploadCTFMicrographs(prot)
                    isActiveCTFMicrographs = prot.isActive()
                elif isinstance(prot, ProtRelionClassify2D) and hasattr(prot, 'outputClasses'):
                    self.uploadClassify2D(prot)
                    isActiveClassify2D = prot.isActive()

            # Check if archive last grid square
            if self.currentGridSquareLastMovieTime is not None:
                timeElapsed = int(time.time() - self.currentGridSquareLastMovieTime)
                self.info("Time elapsed since last movie detected: {0} s".format(timeElapsed))
                # Timeout for uploading last grid square to icat: 2h, 7200 s
                if self.currentGridSquare is not None and timeElapsed > 3600:
                    self.archiveGridSquare(self.currentGridSquare)
                    self.currentGridSquare = None
                    # Check if old grid squares
                    self.archiveOldGridSquares()


            # Update json file
            if self.allParamsJsonFile is not None:
                f = open(self.allParamsJsonFile, "w")
                f.write(json.dumps(self.allParams, indent=4))
                f.close()


            if isActiveImportMovies or isActiveAlignMovies or isActiveCTFMicrographs or isActiveClassify2D:
                finished = False
            else:
                self.info("MonitorISPyB: All upstream activities ended, stopping monitor")
                finished = True

        self.info("MonitorISPyB: end step --------------------------")

        return finished

    def iter_updated_set(self, objSet):
        objSet.load()
        objSet.loadAllProperties()
        for obj in objSet:
            yield obj
        objSet.close()

    def uploadMoviesEPU(self, prot, movieFullPath):
        dictFileNameParameters = UtilsPath.getMovieFileNameParameters(movieFullPath)
        if dictFileNameParameters is None:
            movieName = os.path.basename(movieFullPath)
            self.info("File {0} is not a movie, skipping".format(movieFullPath))
            self.allParams[movieName] = {
                "movieFullPath": movieFullPath,
                "movieId": "not a movie"
            }
        else:
            self.info("dictFileNameParameters: {0}".format(dictFileNameParameters))
            self.movieDirectory = dictFileNameParameters["directory"]
            gridSquare = dictFileNameParameters["gridSquare"]
            prefix = dictFileNameParameters["prefix"]
            date = dictFileNameParameters["date"]
            hour = dictFileNameParameters["hour"]
            movieNumber = dictFileNameParameters["movieNumber"]
            movieName = dictFileNameParameters["movieName"]
            self.info("Import movies: movieName: {0}".format(movieName))
            processDir = os.path.join(os.path.dirname(movieFullPath), "process", movieName)
            if not os.path.exists(processDir):
                try:
                    os.makedirs(processDir, 0o755)
                except OSError as e:
                    processDir = None

            self.movieDirectory = os.path.dirname(movieFullPath)

            micrographSnapshotFullPath, micrographFullPath, xmlMetaDataFullPath, gridSquareSnapshotFullPath = \
                UtilsPath.getMovieJpegMrcXml(movieFullPath)

            startTime = time.time()
            doContinue = True
            while doContinue:
                micrographSnapshotFullPath, micrographFullPath, xmlMetaDataFullPath, gridSquareSnapshotFullPath = \
                    UtilsPath.getMovieJpegMrcXml(movieFullPath)
                if micrographSnapshotFullPath is None or micrographFullPath is None or xmlMetaDataFullPath is None or gridSquareSnapshotFullPath is None:
                    self.info("Import movies: waiting for meta-data files to appear on disk...")
                    timeNow = time.time()
                    deltaTime = timeNow - startTime
                    if deltaTime > 5:
                        self.info("Import movies: Timeout waiting for meta-data files to appear on disk!!!")
                        doContinue = False
                    else:
                        time.sleep(2)
                else:
                    doContinue = False

            self.info("Import movies: micrographSnapshotFullPath: {0}".format(micrographSnapshotFullPath))

            micrographSnapshotPyarchPath = None
            micrographPyarchPath = None
            xmlMetaDataPyarchPath = None
            gridSquareSnapshotPyarchPath = None
            positionX = 0.0
            positionY = 0.0
            dosePerImage = 0.0
            imagesCount = self.imagesCount
            voltage = self.voltage
            magnification = self.magnification
            if micrographFullPath is not None:
                micrographSnapshotPyarchPath = UtilsPath.copyToPyarchPath(micrographSnapshotFullPath)
                xmlMetaDataPyarchPath = UtilsPath.copyToPyarchPath(xmlMetaDataFullPath)
                gridSquareSnapshotPyarchPath = UtilsPath.copyToPyarchPath(gridSquareSnapshotFullPath)

                try:
                    dictMetaData = UtilsPath.getXmlMetaData(xmlMetaDataFullPath)
                    positionX = dictMetaData["positionX"]
                    positionY = dictMetaData["positionY"]
                    dosePerImage = round(float(dictMetaData["dose"]) / 10.0 ** 20 / float(imagesCount), 2)
                except:
                    self.info("ERROR reading XML file {0}".format(xmlMetaDataFullPath))
                    traceback.print_exc()

            sphericalAberration = prot.sphericalAberration.get()
            amplitudeContrast = prot.amplitudeContrast.get()
            samplingRate = prot.samplingRate.get()
            doseInitial = prot.doseInitial.get()
            dosePerFrame = prot.dosePerFrame.get()

            movieId = None
            noTrialsLeft = 5
            uploadSucceeded = False
            while not uploadSucceeded:
                movieObject = None
                try:
                    movieObject = self.client.service.addMovie(
                        proposal=self.proposal,
                        proteinAcronym=self.proteinAcronym,
                        sampleAcronym=self.sampleAcronym,
                        movieDirectory=self.movieDirectory,
                        movieFullPath=movieFullPath,
                        movieNumber=movieNumber,
                        micrographFullPath=micrographPyarchPath,
                        micrographSnapshotFullPath=micrographSnapshotPyarchPath,
                        xmlMetaDataFullPath=xmlMetaDataPyarchPath,
                        voltage=voltage,
                        sphericalAberration=sphericalAberration,
                        amplitudeContrast=amplitudeContrast,
                        magnification=magnification,
                        scannedPixelSize=samplingRate,
                        imagesCount=imagesCount,
                        dosePerImage=dosePerImage,
                        positionX=positionX,
                        positionY=positionY,
                        beamlineName=self.beamlineName,
                        gridSquareSnapshotFullPath=gridSquareSnapshotPyarchPath,
                    )
                except Exception as e:
                    self.info("Error when trying to upload movie!")
                    self.info(e)
                    movieObject = None
                if movieObject is not None:
                    uploadSucceeded = True
                    movieId = movieObject.movieId
                else:
                    if noTrialsLeft == 0:
                        raise RuntimeError("ERROR: failure when trying to upload movie!")
                    else:
                        self.info("ERROR! movieObject is None!")
                        self.info("Sleeping 5 s, and then trying again. Number of trials left: {0}".format(noTrialsLeft))
                        time.sleep(5)
                        noTrialsLeft -= 1

            self.allParams[movieName] = {
                "movieNumber": movieNumber,
                "movieFullPath": movieFullPath,
                "processDir": processDir,
                "date": date,
                "hour": hour,
                "movieId": movieId,
                "imagesCount": imagesCount,
                "dosePerFrame": dosePerFrame,
                "proposal": self.proposal,
                "gridSquare": gridSquare,
                "archived": False,
                "positionX": positionX,
                "positionY": positionY,
            }
            if not "EM_meta_data" in self.allParams:
                self.allParams["EM_meta_data"] = {
                    "EM_directory": prot.filesPath.get(),
                    "EM_protein_acronym": self.proteinAcronym,
                    "EM_voltage": voltage,
                    "EM_magnification": magnification,
                    "EM_images_count": imagesCount,
                    "EM_position_x": positionX,
                    "EM_position_y": positionY,
                    "EM_dose_initial": doseInitial,
                    "EM_spherical_aberration": sphericalAberration,
                    "EM_dose_per_frame": dosePerFrame,
                    "EM_amplitude_contrast": amplitudeContrast,
                    "EM_sampling_rate": samplingRate,
                }
            if not gridSquare in self.allParams:
                self.allParams[gridSquare] = {}
            if not "listGalleryPath" in self.allParams[gridSquare]:
                self.allParams[gridSquare]["listGalleryPath"] = [gridSquareSnapshotFullPath]
            self.info("Import movies done, movieId = {0}".format(self.allParams[movieName]["movieId"]))
            self.currentGridSquareLastMovieTime = time.time()
            if self.currentGridSquare is None:
                self.currentGridSquare = gridSquare
                self.info("New grid square detected: {0}".format(self.currentGridSquare))
            elif self.currentGridSquare != gridSquare:
                # New grid square, archive previous grid square
                self.archiveGridSquare(self.currentGridSquare)
                self.currentGridSquare = None
                # Check if old grid squares
                self.archiveOldGridSquares(gridSquare)

    def uploadMoviesEPUTiff(self, prot, movieFullPath):
        dictFileNameParameters = UtilsPath.getEpuTiffMovieFileNameParameters(movieFullPath)
        if dictFileNameParameters is None:
            movieName = os.path.basename(movieFullPath)
            self.info("File {0} is not a movie, skipping".format(movieFullPath))
            self.allParams[movieName] = {
                "movieFullPath": movieFullPath,
                "movieId": "not a movie"
            }
        else:
            self.info("dictFileNameParameters: {0}".format(dictFileNameParameters))
            self.movieDirectory = dictFileNameParameters["directory"]
            gridSquare = dictFileNameParameters["gridSquare"]
            prefix = dictFileNameParameters["prefix"]
            date = dictFileNameParameters["date"]
            hour = dictFileNameParameters["hour"]
            movieNumber = dictFileNameParameters["movieNumber"]
            movieName = dictFileNameParameters["movieName"]
            self.info("Import movies: movieName: {0}".format(movieName))
            processDir = os.path.join(os.path.dirname(movieFullPath), "process", movieName)
            if not os.path.exists(processDir):
                try:
                    os.makedirs(processDir, 0o755)
                except OSError as e:
                    processDir = None

            self.movieDirectory = os.path.dirname(movieFullPath)
            self.info("movieFullPath: {0}".format(movieFullPath))
            micrographSnapshotFullPath, micrographFullPath, xmlMetaDataFullPath, gridSquareSnapshotFullPath = \
                UtilsPath.getEpuTiffMovieJpegMrcXml(movieFullPath)
            self.info(micrographSnapshotFullPath)
            self.info(micrographFullPath)
            self.info(xmlMetaDataFullPath)
            self.info(gridSquareSnapshotFullPath)
            startTime = time.time()
            doContinue = True
            while doContinue:
                micrographSnapshotFullPath, micrographFullPath, xmlMetaDataFullPath, gridSquareSnapshotFullPath = \
                    UtilsPath.getEpuTiffMovieJpegMrcXml(movieFullPath)
                if micrographSnapshotFullPath is None or micrographFullPath is None or xmlMetaDataFullPath is None or gridSquareSnapshotFullPath is None:
                    self.info("Import movies: waiting for meta-data files to appear on disk...")
                    timeNow = time.time()
                    deltaTime = timeNow - startTime
                    if deltaTime > 5:
                        self.info("Import movies: Timeout waiting for meta-data files to appear on disk!!!")
                        doContinue = False
                    else:
                        time.sleep(2)
                else:
                    doContinue = False
            # micrographFullPath = None
            # self.info("Import movies: micrographSnapshotFullPath: {0}".format(micrographSnapshotFullPath))

            micrographSnapshotPyarchPath = None
            micrographPyarchPath = None
            xmlMetaDataPyarchPath = None
            gridSquareSnapshotPyarchPath = None
            positionX = 0.0
            positionY = 0.0
            dosePerImage = 0.0
            imagesCount = self.imagesCount
            voltage = self.voltage
            magnification = self.magnification
            if micrographFullPath is not None:
                micrographSnapshotPyarchPath = UtilsPath.copyToPyarchPath(micrographSnapshotFullPath)
                xmlMetaDataPyarchPath = UtilsPath.copyToPyarchPath(xmlMetaDataFullPath)
                gridSquareSnapshotPyarchPath = UtilsPath.copyToPyarchPath(gridSquareSnapshotFullPath)

                try:
                    dictMetaData = UtilsPath.getXmlMetaData(xmlMetaDataFullPath)
                    positionX = dictMetaData["positionX"]
                    positionY = dictMetaData["positionY"]
                    dosePerImage = round(float(dictMetaData["dose"]) / 10.0 ** 20 / float(imagesCount), 2)
                except:
                    self.info("ERROR reading XML file {0}".format(xmlMetaDataFullPath))
                    traceback.print_exc()

            sphericalAberration = prot.sphericalAberration.get()
            amplitudeContrast = prot.amplitudeContrast.get()
            samplingRate = prot.samplingRate.get()
            doseInitial = prot.doseInitial.get()
            dosePerFrame = prot.dosePerFrame.get()

            movieId = None
            noTrialsLeft = 5
            uploadSucceeded = False
            while not uploadSucceeded:
                movieObject = None
                try:
                    movieObject = self.client.service.addMovie(
                        proposal=self.proposal,
                        proteinAcronym=self.proteinAcronym,
                        sampleAcronym=self.sampleAcronym,
                        movieDirectory=self.movieDirectory,
                        movieFullPath=movieFullPath,
                        movieNumber=movieNumber,
                        micrographFullPath=micrographPyarchPath,
                        micrographSnapshotFullPath=micrographSnapshotPyarchPath,
                        xmlMetaDataFullPath=xmlMetaDataPyarchPath,
                        voltage=voltage,
                        sphericalAberration=sphericalAberration,
                        amplitudeContrast=amplitudeContrast,
                        magnification=magnification,
                        scannedPixelSize=samplingRate,
                        imagesCount=imagesCount,
                        dosePerImage=dosePerImage,
                        positionX=positionX,
                        positionY=positionY,
                        beamlineName=self.beamlineName,
                        gridSquareSnapshotFullPath=gridSquareSnapshotPyarchPath,
                    )
                except Exception as e:
                    self.info("Error when trying to upload movie!")
                    self.info(e)
                    movieObject = None
                if movieObject is not None:
                    uploadSucceeded = True
                    movieId = movieObject.movieId
                else:
                    if noTrialsLeft == 0:
                        raise RuntimeError("ERROR: failure when trying to upload movie!")
                    else:
                        self.info("ERROR! movieObject is None!")
                        self.info("Sleeping 5 s, and then trying again. Number of trials left: {0}".format(noTrialsLeft))
                        time.sleep(5)
                        noTrialsLeft -= 1

            self.allParams[movieName] = {
                "movieNumber": movieNumber,
                "movieFullPath": movieFullPath,
                "processDir": processDir,
                "date": date,
                "hour": hour,
                "movieId": movieId,
                "imagesCount": imagesCount,
                "dosePerFrame": dosePerFrame,
                "proposal": self.proposal,
                "gridSquare": gridSquare,
                "archived": False,
                "positionX": positionX,
                "positionY": positionY,
            }
            if not "EM_meta_data" in self.allParams:
                self.allParams["EM_meta_data"] = {
                    "EM_directory": prot.filesPath.get(),
                    "EM_protein_acronym": self.proteinAcronym,
                    "EM_voltage": voltage,
                    "EM_magnification": magnification,
                    "EM_images_count": imagesCount,
                    "EM_position_x": positionX,
                    "EM_position_y": positionY,
                    "EM_dose_initial": doseInitial,
                    "EM_spherical_aberration": sphericalAberration,
                    "EM_dose_per_frame": dosePerFrame,
                    "EM_amplitude_contrast": amplitudeContrast,
                    "EM_sampling_rate": samplingRate,
                }
            if not gridSquare in self.allParams:
                self.allParams[gridSquare] = {}
            # if not "listGalleryPath" in self.allParams[gridSquare]:
            #     self.allParams[gridSquare]["listGalleryPath"] = [gridSquareSnapshotFullPath]
            self.info("Import movies done, movieId = {0}".format(self.allParams[movieName]["movieId"]))
            self.currentGridSquareLastMovieTime = time.time()
            if self.currentGridSquare is None:
                self.currentGridSquare = gridSquare
                self.info("New grid square detected: {0}".format(self.currentGridSquare))
            elif self.currentGridSquare != gridSquare:
                # New grid square, archive previous grid square
                self.archiveGridSquare(self.currentGridSquare)
                self.currentGridSquare = None
                # Check if old grid squares
                self.archiveOldGridSquares(gridSquare)

    def uploadMoviesSerialEM(self, prot, movieFullPath):
        dictFileNameParameters = UtilsPath.getSerialEMMovieFileNameParameters(str(prot.filesPath), movieFullPath)
        if dictFileNameParameters is None:
            movieName = os.path.basename(movieFullPath)
            self.info("File {0} is not a movie, skipping".format(movieFullPath))
            self.allParams[movieName] = {
                "movieFullPath": movieFullPath,
                "movieId": "not a movie"
            }
        else:
            self.info("dictFileNameParameters: {0}".format(dictFileNameParameters))
            self.movieDirectory = dictFileNameParameters["directory"]
            prefix = dictFileNameParameters["prefix"]
            movieNumber = dictFileNameParameters["movieNumber"]
            movieName = dictFileNameParameters["movieName"]
            self.info("Import movies: movieName: {0}".format(movieName))
            processDir = os.path.join(os.path.dirname(movieFullPath), "process", movieName)
            if not os.path.exists(processDir):
                try:
                    os.makedirs(processDir, 0o755)
                except OSError as e:
                    processDir = None
            self.movieDirectory = os.path.dirname(movieFullPath)
            # Get SerialEM metadata
            mdocFullPath = movieFullPath + ".mdoc"

            startTime = time.time()
            doContinue = True
            while doContinue:
                if not os.path.exists(mdocFullPath):
                    self.info("Import movies: waiting for meta-data files to appear on disk...")
                    timeNow = time.time()
                    deltaTime = timeNow - startTime
                    if deltaTime > 30:
                        self.info("Import movies: Timeout waiting for meta-data files to appear on disk!!!")
                        doContinue = False
                    else:
                        time.sleep(5)
                else:
                    doContinue = False
                    self.info("Import movies: mdocFullPath: {0}".format(mdocFullPath))
                    dictMetaData = UtilsPath.getMdocMetaData(mdocFullPath)
                    self.positionX, self.positionY = dictMetaData['StagePosition'].split(' ')
                    self.collectionDate, self.collectionTime = dictMetaData['DateTime'].split('  ')

            voltage = self.voltage
            magnification = self.magnification
            imagesCount = self.imagesCount
            positionX = self.positionX
            positionY = self.positionY
            date = self.collectionDate.strip()
            hour = self.collectionTime.strip()
            micrographSnapshotFullPath = None
            micrographFullPath = None
            xmlMetaDataFullPath = None
            gridSquareSnapshotFullPath = None
            micrographSnapshotPyarchPath = None
            micrographPyarchPath = None
            xmlMetaDataPyarchPath = None
            gridSquareSnapshotPyarchPath = "/tmp/tt.png"
            dosePerImage = None
            sphericalAberration = prot.sphericalAberration.get()
            amplitudeContrast = prot.amplitudeContrast.get()
            samplingRate = prot.samplingRate.get()
            dosePerFrame = prot.dosePerFrame.get()
            doseInitial = prot.doseInitial.get()
            #
            self.info("proposal: {0}".format(self.proposal))
            self.info("proteinAcronym: {0}".format(self.proteinAcronym))
            self.info("sampleAcronym: {0}".format(self.sampleAcronym))
            self.info("movieDirectory: {0}".format(self.movieDirectory))
            self.info("movieFullPath: {0}".format(movieFullPath))
            self.info("movieNumber: {0}".format(movieNumber))
            self.info("micrographFullPath: {0}".format(micrographFullPath))
            self.info("micrographSnapshotFullPath: {0}".format(micrographSnapshotFullPath))
            self.info("xmlMetaDataFullPath: {0}".format(xmlMetaDataFullPath))
            self.info("voltage: {0}".format(voltage))
            self.info("sphericalAberration: {0}".format(sphericalAberration))
            self.info("amplitudeContrast: {0}".format(amplitudeContrast))
            self.info("magnification: {0}".format(magnification))
            self.info("samplingRate: {0}".format(samplingRate))
            self.info("imagesCount: {0}".format(imagesCount))
            self.info("dosePerImage: {0}".format(dosePerImage))
            self.info("positionX: {0}".format(positionX))
            self.info("positionY: {0}".format(positionY))
            self.info("beamlineName: {0}".format(self.beamlineName))
            self.info("gridSquareSnapshotFullPath: {0}".format(gridSquareSnapshotFullPath))
            movieObject = self.client.service.addMovie(proposal=self.proposal,
                                                       proteinAcronym=self.proteinAcronym,
                                                       sampleAcronym=self.sampleAcronym,
                                                       movieDirectory=self.movieDirectory,
                                                       movieFullPath=movieFullPath,
                                                       movieNumber=movieNumber,
                                                       micrographFullPath=micrographPyarchPath,
                                                       micrographSnapshotFullPath=micrographSnapshotPyarchPath,
                                                       xmlMetaDataFullPath=xmlMetaDataPyarchPath,
                                                       voltage=voltage,
                                                       sphericalAberration=sphericalAberration,
                                                       amplitudeContrast=amplitudeContrast,
                                                       magnification=magnification,
                                                       scannedPixelSize=samplingRate,
                                                       imagesCount=imagesCount,
                                                       dosePerImage=dosePerImage,
                                                       positionX=positionX,
                                                       positionY=positionY,
                                                       beamlineName=self.beamlineName,
                                                       gridSquareSnapshotFullPath=gridSquareSnapshotPyarchPath,
                                                       )

            if movieObject is not None:
                movieId = movieObject.movieId
            else:
                raise RuntimeError("ISPyB Movie object is None!")

            gridSquare = "GridSquare_112345"
            self.allParams[movieName] = {
                "movieNumber": movieNumber,
                "movieFullPath": movieFullPath,
                "processDir": processDir,
                "date": date,
                "hour": hour,
                "movieId": movieId,
                "imagesCount": imagesCount,
                "dosePerFrame": dosePerFrame,
                "proposal": self.proposal,
                "gridSquare": gridSquare,
                "archived": False,
                "positionX": positionX,
                "positionY": positionY,
            }
            if not "EM_meta_data" in self.allParams:
                self.allParams["EM_meta_data"] = {
                    "EM_directory": prot.filesPath.get(),
                    "EM_protein_acronym": self.proteinAcronym,
                    "EM_voltage": voltage,
                    "EM_magnification": magnification,
                    "EM_images_count": imagesCount,
                    "EM_position_x": positionX,
                    "EM_position_y": positionY,
                    "EM_dose_initial": doseInitial,
                    "EM_spherical_aberration": sphericalAberration,
                    "EM_dose_per_frame": dosePerFrame,
                    "EM_amplitude_contrast": amplitudeContrast,
                    "EM_sampling_rate": samplingRate,
                }
            #     if not gridSquare in self.allParams:
            #         self.allParams[gridSquare] = {}
            #     if not "listGalleryPath" in self.allParams[gridSquare]:
            #         self.allParams[gridSquare]["listGalleryPath"] = [gridSquareSnapshotFullPath]
            #     self.info("Import movies done, movieId = {0}".format(self.allParams[movieName]["movieId"]))
            #     self.currentGridSquareLastMovieTime = time.time()
            #     if self.currentGridSquare is None:
            #         self.currentGridSquare = gridSquare
            #         self.info("New grid square detected: {0}".format(self.currentGridSquare))
            #     elif self.currentGridSquare != gridSquare:
            #         # New grid square, archive previous grid square
            #         self.archiveGridSquare(self.currentGridSquare)
            #         self.currentGridSquare = None
            #         # Check if old grid squares
            #         self.archiveOldGridSquares(gridSquare)

    def uploadImportMovies(self, prot):
        for movieFullPath in prot.getMatchFiles():
            listMovieFullPath = []
            for movieName in self.allParams:
                if "movieFullPath" in self.allParams[movieName] and "movieId" in self.allParams[movieName]:
                    if self.allParams[movieName]["movieId"] is not None:
                        listMovieFullPath.append(self.allParams[movieName]["movieFullPath"])
#            listMovieFullPath = [ self.allParams[movieName]["movieFullPath"] for movieName in self.allParams if "movieFullPath" in self.allParams[movieName]]
            if movieFullPath in listMovieFullPath:
                pass
                #self.info("Movie already uploaded: {0}".format(movieFullPath))
            else:
                self.info("Import movies: movieFullPath: {0}".format(movieFullPath))
                if self.dataType == 0: # "EPU"
                    self.uploadMoviesEPU(prot, movieFullPath)
                if self.dataType == 1: # "EPU_TIFF"
                    self.uploadMoviesEPUTiff(prot, movieFullPath)
                elif self.dataType == 2: # "SERIALEM"
                    self.uploadMoviesSerialEM(prot, movieFullPath)
                else:
                    raise RuntimeError("Unknown data type: {0}".format(self.dataType))

    def uploadAlignMovies(self, prot):
        self.info("ESRF ISPyB upload motion corr results")
        for micrograph in self.iter_updated_set(prot.outputMicrographs):
            micrographFullPath = os.path.join(self.currentDir, micrograph.getFileName())
            self.info("*"*80)
            self.info("Motion corr micrographFullPath: {0}".format(micrographFullPath))
            if self.dataType == 0: # "EPU"
                dictFileNameParameters = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            elif self.dataType == 1:  # "EPU_TIFF"
                dictFileNameParameters = UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            elif self.dataType == 2: # "SERIALEM"
                dictFileNameParameters = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            else:
                raise RuntimeError("Unknown data type: {0}".format(self.dataType))
            movieName = dictFileNameParameters["movieName"]
            # self.info("Motion corr movie name: {0}".format(movieName))
            if movieName in self.allParams and not "motionCorrectionId" in self.allParams[movieName]:
                self.info("Align movies: movie {0}".format(os.path.basename(self.allParams[movieName]["movieFullPath"])))
                movieFullPath = self.allParams[movieName]["movieFullPath"]
                if self.dataType == 0:  # "EPU"
                    dictResult = UtilsPath.getAlignMoviesPngLogFilePath(micrographFullPath)
                elif self.dataType == 1:  # "EPU_TIFF"
                    dictResult = UtilsPath.getEpuTiffAlignMoviesPngLogFilePath(micrographFullPath)
                elif self.dataType == 2: # "SERIALEM"
                    dictResult = UtilsPath.getSerialEMAlignMoviesPngLogFilePath(micrographFullPath)
                else:
                    raise RuntimeError("Unknown data type: {0}".format(self.dataType))
                driftPlotFullPath = dictResult["globalShiftPng"]
                if "doseWeightMrc" in dictResult:
                    correctedDoseMicrographFullPath = dictResult["doseWeightMrc"]
                else:
                    correctedDoseMicrographFullPath = None
                if "thumbnailPng" in dictResult:
                    micrographSnapshotFullPath = dictResult["thumbnailPng"]
                else:
                    micrographSnapshotFullPath = None
                dictShift = UtilsPath.getShiftData(micrographFullPath)
                if "totalMotion" in dictShift:
                    totalMotion = dictShift["totalMotion"]
                else:
                    totalMotion = None
                if "averageMotionPerFrame" in dictShift:
                    averageMotionPerFrame = dictShift["averageMotionPerFrame"]
                else:
                    averageMotionPerFrame = None
                logFileFullPath = dictResult["logFileFullPath"]
                firstFrame = self.alignFrame0
                lastFrame = self.alignFrameN
                dosePerFrame = self.allParams[movieName]["dosePerFrame"]
                doseWeight = None
                driftPlotPyarchPath = UtilsPath.copyToPyarchPath(driftPlotFullPath)
                micrographPyarchPath = None
                correctedDoseMicrographPyarchPath = None
                micrographSnapshotPyarchPath = UtilsPath.copyToPyarchPath(micrographSnapshotFullPath)
                logFilePyarchPath = UtilsPath.copyToPyarchPath(logFileFullPath)

                if self.allParams[movieName]["processDir"] is not None:
                    shutil.copy(micrographFullPath, self.allParams[movieName]["processDir"])
                    shutil.copy(correctedDoseMicrographFullPath, self.allParams[movieName]["processDir"])
                    shutil.copy(logFileFullPath, self.allParams[movieName]["processDir"])
                noTrialsLeft = 5
                uploadSucceeded = False
                while not uploadSucceeded:
                    motionCorrectionObject = None
                    try:
                        motionCorrectionObject = self.client.service.addMotionCorrection(
                            proposal=self.proposal,
                            movieFullPath=movieFullPath,
                            firstFrame=firstFrame,
                            lastFrame=lastFrame,
                            dosePerFrame=dosePerFrame,
                            doseWeight=doseWeight,
                            totalMotion=totalMotion,
                            averageMotionPerFrame=averageMotionPerFrame,
                            driftPlotFullPath=driftPlotPyarchPath,
                            micrographFullPath=micrographPyarchPath,
                            correctedDoseMicrographFullPath=correctedDoseMicrographPyarchPath,
                            micrographSnapshotFullPath=micrographSnapshotPyarchPath,
                            logFileFullPath=logFilePyarchPath
                        )
                    except Exception as e:
                        self.info("Error when trying to upload motion correction!")
                        self.info(e)
                        motionCorrectionObject = None
                    if motionCorrectionObject is not None:
                        uploadSucceeded = True
                        motionCorrectionId = motionCorrectionObject.motionCorrectionId
                    else:
                        if noTrialsLeft == 0:
                            raise RuntimeError("ERROR: failure when trying to upload motion correction!")
                        else:
                            self.info("ERROR! motionCorrectionObject is None!")
                            self.info("Sleeping 5 s, and then trying again. Number of trials left: {0}".format(noTrialsLeft))
                            time.sleep(5)
                            noTrialsLeft -= 1
                time.sleep(0.1)
                self.allParams[movieName]["motionCorrectionId"] = motionCorrectionId
                self.allParams[movieName]["totalMotion"] = totalMotion
                self.allParams[movieName]["averageMotionPerFrame"] = averageMotionPerFrame

                self.info("Align movies done, motionCorrectionId = {0}".format(motionCorrectionId))

    def uploadCTFMicrographs(self, prot):
        self.info("ESRF ISPyB upload CTF results")
        workingDir = os.path.join(self.currentDir, str(prot.workingDir))
        for ctf in self.iter_updated_set(prot.outputCTF):
            micrographFullPath = ctf.getMicrograph().getFileName()
            if self.dataType == 0: # "EPU"
                dictFileNameParameters = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            elif self.dataType == 1: # "EPU"
                dictFileNameParameters = UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            elif self.dataType == 2: # "SERIALEM"
                dictFileNameParameters = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(micrographFullPath)
            else:
                raise RuntimeError("Unknown data type: {0}".format(self.dataType))
            movieName = dictFileNameParameters["movieName"]
            if movieName in self.allParams and "motionCorrectionId" in self.allParams[movieName] and not "CTFid" in self.allParams[movieName]:
                self.info("CTF: movie {0}".format(os.path.basename(self.allParams[movieName]["movieFullPath"])))
                movieFullPath = self.allParams[movieName]["movieFullPath"]
                spectraImageSnapshotFullPath = None
                spectraImageSnapshotPyarchPath = None
                spectraImageFullPath = None
                spectraImagePyarchPath = None
                defocusU = None
                defocusV = None
                angle = None
                crossCorrelationCoefficient = None
                phaseShift = None
                resolutionLimit = None
                estimatedBfactor = None

                dictResults = UtilsPath.getCtfMetaData(workingDir, micrographFullPath)
                spectraImageSnapshotFullPath = dictResults["spectraImageSnapshotFullPath"]
                spectraImageSnapshotPyarchPath = UtilsPath.copyToPyarchPath(spectraImageSnapshotFullPath)
                spectraImageFullPath = dictResults["spectraImageFullPath"]
                spectraImagePyarchPath = None
                defocusU = dictResults["Defocus_U"]
                defocusV = dictResults["Defocus_V"]
                angle = dictResults["Angle"]
                crossCorrelationCoefficient = dictResults["CCC"]
                phaseShift = dictResults["Phase_shift"]
                resolutionLimit = dictResults["resolutionLimit"]
                estimatedBfactor = dictResults["estimatedBfactor"]
                if self.allParams[movieName]["processDir"] is not None:
                    shutil.copy(spectraImageFullPath, self.allParams[movieName]["processDir"])
                    shutil.copy(dictResults["logFilePath"], self.allParams[movieName]["processDir"])

                logFilePath = UtilsPath.copyToPyarchPath(dictResults["logFilePath"])
                # self.info("proposal : {0}".format(self.proposal))
                # self.info("movieFullPath : {0}".format(movieFullPath))
                # self.info("spectraImageSnapshotFullPath : {0}".format(spectraImageSnapshotPyarchPath))
                # self.info("spectraImageFullPath : {0}".format(spectraImagePyarchPath))
                # self.info("defocusU : {0}".format(defocusU))
                # self.info("defocusV : {0}".format(defocusV))
                # self.info("angle : {0}".format(angle))
                # self.info("crossCorrelationCoefficient : {0}".format(crossCorrelationCoefficient))
                # self.info("resolutionLimit : {0}".format(resolutionLimit))
                # self.info("estimatedBfactor : {0}".format(estimatedBfactor))
                # self.info("logFilePath : {0}".format(logFilePath))

                ctfObject = self.client.service.addCTF(proposal=self.proposal,
                                    movieFullPath=movieFullPath,
                                    spectraImageSnapshotFullPath=spectraImageSnapshotPyarchPath,
                                    spectraImageFullPath=spectraImagePyarchPath,
                                    defocusU=defocusU,
                                    defocusV=defocusV,
                                    angle=angle,
                                    crossCorrelationCoefficient=crossCorrelationCoefficient,
                                    resolutionLimit=resolutionLimit,
                                    estimatedBfactor=estimatedBfactor,
                                    logFilePath=logFilePath)

                if ctfObject is not None:
                    CTFid = ctfObject.CTFid
                else:
                    raise RuntimeError("ISPyB: ctfObject is None!")

                time.sleep(0.1)

                self.allParams[movieName]["CTFid"] = CTFid
                self.allParams[movieName]["phaseShift"] = phaseShift
                self.allParams[movieName]["defocusU"] = defocusU
                self.allParams[movieName]["defocusV"] = defocusV
                self.allParams[movieName]["angle"] = angle
                self.allParams[movieName]["crossCorrelationCoefficient"] = crossCorrelationCoefficient
                self.allParams[movieName]["resolutionLimit"] = resolutionLimit

                self.info("CTF done, CTFid = {0}".format(CTFid))


    def uploadClassify2D(self, prot):
        self.info("ISPyB upload 2D classification results")
        workingDir = os.path.join(self.currentDir, str(prot.workingDir))
        extraDirectory = os.path.join(workingDir, "extra")
        pathToInputParticlesStarFile = os.path.join(extraDirectory, "input_particles.sqlite")
        print("Input data")


    def archiveGridSquare(self, gridSquareToBeArchived):
        # Archive remaining movies
        self.info("Archiving grid square: {0}".format(gridSquareToBeArchived))
        listPathsToBeArchived = []
        sumPositionX = 0.0
        sumPositionY = 0.0
        indexPosition = 0
        for movieName in self.allParams:
            if "gridSquare" in self.allParams[movieName] and self.allParams[movieName]["gridSquare"] == gridSquareToBeArchived and not self.allParams[movieName]["archived"]:
                listPathsToBeArchived.append(self.allParams[movieName]["movieFullPath"])
                self.allParams[movieName]["archived"] = True
                try:
                    sumPositionX += float(self.allParams[movieName]["positionX"])
                    sumPositionY += float(self.allParams[movieName]["positionY"])
                    indexPosition += 1
                except:
                    pass
        noImagesToBeArchived = len(listPathsToBeArchived)
        if noImagesToBeArchived > 0:
            if indexPosition > 0:
                meanPositionX = sumPositionX / indexPosition
                meanPositionY = sumPositionY / indexPosition
            else:
                meanPositionX = None
                meanPositionY = None
            dictIcatMetaData = dict(self.allParams["EM_meta_data"])
            dictIcatMetaData["EM_position_x"] = meanPositionX
            dictIcatMetaData["EM_position_y"] = meanPositionY
            directory = dictIcatMetaData["EM_directory"]
            listGalleryPath = self.allParams[gridSquareToBeArchived]["listGalleryPath"]
            dataSetName = "{0}_{1}".format(gridSquareToBeArchived, round(time.time()))
            self.allParams[dataSetName] = dictIcatMetaData
            self.info("listPathsToBeArchived: {0}".format(pprint.pformat(listPathsToBeArchived)))
            self.info("directory: {0}".format(directory))
            self.info("self.proposal: {0}".format(self.proposal))
            self.info("self.sampleAcronym: {0}".format(self.sampleAcronym))
            self.info("dataSetName: {0}".format(dataSetName))
            self.info("dictIcatMetaData: {0}".format(pprint.pformat(dictIcatMetaData)))
            errorMessage = UtilsIcat.uploadToIcat(listPathsToBeArchived, directory, self.proposal,
                                                  self.sampleAcronym, dataSetName, dictIcatMetaData,
                                                  listGalleryPath)
            if errorMessage is not None:
                self.info("ERROR during icat upload!")
                self.info(errorMessage)

    def archiveOldGridSquares(self, gridSquareNotToArchive=None):
        self.info("Archiving old grid squares (in any)")
        # Check if there are remaining grid squares to be uploaded:
        dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(self.allParams, gridSquareNotToArchive)
        for gridSquareToBeArchived in dictGridSquares:
            self.archiveGridSquare(gridSquareToBeArchived)

    def archiveGainAndDefectMap(self):
        if self.defectMapPath != "" or self.gainFilePath != "":
            self.info("Archiving gain and defect map files")
            if not "GainAndDefectMap" in self.allParams:
                self.allParams["GainAndDefectMap"] = {}
                if self.defectMapPath != "":
                    self.allParams["GainAndDefectMap"]["defectMapPath"] = self.defectMapPath
                if self.gainFilePath != "":
                    self.allParams["GainAndDefectMap"]["gainFilPath"] = self.gainFilePath
                self.allParams["GainAndDefectMap"]["archived"] = False
            if not self.allParams["GainAndDefectMap"]["archived"]:
                listPathsToBeArchived = [self.defectMapPath, self.gainFilePath]
                directory = os.path.dirname(self.defectMapPath)
                dictIcatMetaData = {
                    "EM_directory": directory,
                    "EM_protein_acronym": self.proteinAcronym,
                    "EM_voltage": self.voltage,
                    "EM_magnification": self.magnification
                }
                dataSetName = "GainAndDefectMap"
                listGalleryPath = []
                errorMessage = UtilsIcat.uploadToIcat(
                    listPathsToBeArchived, directory, self.proposal,
                    self.sampleAcronym, dataSetName, dictIcatMetaData,
                    listGalleryPath)
                if errorMessage is None:
                    self.allParams["GainAndDefectMap"]["archived"] = True
                else:
                    self.info("WARNING! Couldn't archive gain and defect map")

