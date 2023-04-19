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
import shutil
import threading
import collections


import pyworkflow.protocol.params as params

from pyworkflow import VERSION_1_1
from pyworkflow.protocol import getUpdatedProtocol
from emfacilities.protocols import ProtMonitor, Monitor, PrintNotifier
from pwem.protocols import ProtImportMovies
from motioncorr.protocols import ProtMotionCorr

from esrf.utils.esrf_utils_icat import UtilsIcat
from esrf.utils.esrf_utils_path import UtilsPath

# Fix for GPFS problem
shutil._USE_CP_SENDFILE = False


class ProtMonitorIcatTomo(ProtMonitor):
    """
    Monitor to communicated with ICAT system at ESRF for tomo data.
    """

    _label = "monitor to ICAT for tomo at the ESRF"
    _lastUpdateVersion = VERSION_1_1

    def __init__(self, **kwargs):
        ProtMonitor.__init__(self, **kwargs)

    def _defineParams(self, form):
        ProtMonitor._defineParams(self, form)

        section1 = form.addSection(label="Names")

        section1.addParam(
            "proposal",
            params.StringParam,
            default="unknown",
            label="Proposal",
            important=True,
            help="Proposal",
        )

        section1.addParam(
            "sampleAcronym",
            params.StringParam,
            default="unknown",
            label="Sample acronym",
            important=True,
            help="Name of the sample acronym",
        )

        section1.addParam(
            "proteinAcronym",
            params.StringParam,
            default="unknown",
            label="Protein acronym",
            important=True,
            help="Name of the protein acronym",
        )

        section2 = form.addSection(label="Experiment")

        section2.addParam(
            "voltage",
            params.IntParam,
            default=300000,
            label="Voltage",
            important=True,
            help="Voltage in [V]",
        )

        section2.addParam(
            "magnification",
            params.IntParam,
            default=100000,
            label="Nominal magnification",
            important=True,
            help="Nominal magnification",
        )

        section2.addParam(
            "imagesCount",
            params.IntParam,
            default=40,
            label="Images count",
            important=True,
            help="Number of images per movie",
        )

        section2.addParam(
            "alignFrame0",
            params.IntParam,
            default=1,
            label="Align Frame 0",
            help="Starting frame for motion correction",
        )

        section2.addParam(
            "alignFrameN",
            params.IntParam,
            default=-1,
            label="Align Frame N",
            help="End frame for motion correction (-1 = all frames)",
        )

        section2.addParam(
            "gainFilePath",
            params.StringParam,
            default="",
            label="Gain file",
            help="Gain file path for Motioncor 2",
        )

        section2.addParam(
            "defectMapPath",
            params.StringParam,
            default="",
            label="Defect map file",
            help="Defect map path for Motioncor 2",
        )

        section2.addParam(
            "allParamsJsonFile",
            params.StringParam,
            default="",
            label="All parameters json file",
            help="Json file containing all parameters from processing.",
        )

    # --------------------------- INSERT steps functions ------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep("monitorStep")

    # --------------------------- STEPS functions -------------------------------
    def monitorStep(self):
        monitor = MonitorESRFIcatTomo(
            self,
            workingDir=self._getPath(),
            samplingInterval=30,  # 30 seconds                                        # samplingInterval=self.samplingInterval.get(),
            monitorTime=4 * 24 * 60,
        )  # 4*24 H max monitor time

        monitor.addNotifier(PrintNotifier())
        monitor.loop()


class MonitorESRFIcatTomo(Monitor):
    """This will be monitoring a CTF estimation protocol.
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
        self.proposal = protocol.proposal.get()
        self.proteinAcronym = protocol.proteinAcronym.get()
        self.sampleAcronym = protocol.sampleAcronym.get()
        self.movieDirectory = None
        self.currentDir = os.getcwd()
        self.currentGridSquare = None
        self.currentGridSquareLastMovieTime = None
        self.beamlineName = "cm01"
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
                    self.all_params = collections.OrderedDict(dictAllParams)
                except BaseException:
                    self.all_params = collections.OrderedDict()
            else:
                self.all_params = collections.OrderedDict()
        else:
            self.allParamsJsonFile = None
            self.all_params = collections.OrderedDict()

    def step(self):
        self.info("MonitorISPyB: start step ------------------------")
        self.info("Number of movies in all params: {0}".format(len(self.all_params)))

        # Check if we should archive gain an defect maps
        # self.archiveGainAndDefectMap()

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

            # Check if we should archive any grid squares
            # archivedGridSquare = self.archiveOldGridSquare()
            # if archivedGridSquare is not None:
            #     self.info("Grid square archived: {0}".format(archivedGridSquare))
            #     self.updateJsonFile()
            # else:
            #     self.info("No grid square to archive.")

            for n in nodes:
                prot = n.run
                self.info("*" * 80)
                self.info("Protocol name: {0}".format(prot.getRunName()))

                if isinstance(prot, ProtImportMovies):
                    self.uploadImportMovies(prot)
                    isActiveImportMovies = prot.isActive()
                # elif isinstance(prot, XmippProtMovieMaxShift) and hasattr(prot, 'outputMicrographs'):
                elif isinstance(prot, ProtMotionCorr) and hasattr(
                    prot, "outputMicrographs"
                ):
                    self.uploadAlignMovies(prot)
                    isActiveAlignMovies = prot.isActive()
                # elif isinstance(prot, ProtCTFMicrographs) and hasattr(
                #     prot, "outputCTF"
                # ):
                #     self.uploadCTFMicrographs(prot)
                #     isActiveCTFMicrographs = prot.isActive()
                # elif (
                #     isinstance(prot, ProtClassify2D)
                #     and hasattr(prot, "outputClasses")
                #     and not prot.getObjId() in self.all_params
                # ):
                #     self.uploadClassify2D(prot)
                #     isActiveClassify2D = prot.isActive()

            if isActiveImportMovies or isActiveAlignMovies or isActiveCTFMicrographs:
                finished = False
            else:
                self.info(
                    "MonitorIcatTomo: All upstream activities ended, stopping monitor"
                )
                finished = True
            self.updateJsonFile()
        self.info("MonitorIcatTomo: end step --------------------------")

        return finished

    def noInterrupt(self, path, obj):
        with open(path, "w") as fd:
            fd.write(obj)

    def updateJsonFile(self):
        if self.allParamsJsonFile is not None:
            thread = threading.Thread(
                target=self.noInterrupt,
                args=(self.allParamsJsonFile, json.dumps(self.all_params, indent=4)),
            )
            thread.start()
            thread.join()

    def iter_updated_set(self, objSet):
        objSet.load()
        objSet.loadAllProperties()
        for obj in objSet:
            yield obj
        objSet.close()

    def uploadImportMovies(self, prot):
        for movie_full_path in prot.getMatchFiles():
            list_movie_full_path = []
            for movieName in self.all_params:
                if (
                    "movieFullPath" in self.all_params[movieName]
                ):
                    list_movie_full_path.append(
                        self.all_params[movieName]["movieFullPath"]
                    )
            #            listMovieFullPath = [ self.all_params[movieName]["movieFullPath"] for movieName in self.all_params if "movieFullPath" in self.all_params[movieName]]
            if movie_full_path in list_movie_full_path:
                pass
                self.info("Movie already uploaded: {0}".format(movie_full_path))
            else:
                self.info("Import movies: movieFullPath: {0}".format(movie_full_path))
                self.archiveMovieInIcatPlus(prot, movie_full_path)

    def uploadAlignMovies(self, prot):
        self.protocol.info("ESRF ISPyB upload motion corr results")

    def archiveMovieInIcatPlus(self, prot, movie_full_path):
        spherical_aberration = prot.sphericalAberration.get()
        amplitude_contrast = prot.amplitudeContrast.get()
        sampling_rate = prot.samplingRate.get()
        dose_initial = prot.doseInitial.get()
        dose_per_frame = prot.dosePerFrame.get()
        dict_movie = UtilsPath.getTomoMovieFileNameParameters(movie_full_path)
        file_name = dict_movie["file_name"]
        movie_name = dict_movie["movie_name"]
        movie_number = dict_movie["movie_number"]
        grid_name = dict_movie["grid_name"]
        tilt_angle = dict_movie["tilt_angle"]
        tilt_serie_number = dict_movie["tilt_serie_number"]
        icat_movie_directory_path = UtilsPath.createIcatDirectory(movie_full_path)
        self.info(f"Archiving movie: movieFullPath: {movie_full_path}")
        dictMetadata = {
            "Sample_name": f"{grid_name}_Position_{tilt_serie_number}",
            "EM_amplitude_contrast": amplitude_contrast,
            "EM_dose_initial": dose_initial,
            "EM_dose_per_frame": dose_per_frame,
            "EM_images_count": self.imagesCount,
            "EM_magnification": self.magnification,
            "EM_protein_acronym": self.proteinAcronym,
            "EM_sampling_rate": sampling_rate,
            "EM_spherical_aberration": spherical_aberration,
            "EM_voltage": self.voltage,
            "EM_grid_name": grid_name,
            "EM_tilt_angle": tilt_angle
        }
        UtilsIcat.uploadToIcatPlus(
            directory=str(icat_movie_directory_path),
            proposal=self.proposal,
            dataSetName=f"{movie_number:03d}",
            dictMetadata=dictMetadata
        )
        self.all_params[movie_name] = {
            "tiltSerieNumber": tilt_serie_number,
            "movieFullPath": movie_full_path,
            "movieNumber": movie_number,
            "tiltAngle": tilt_angle,
            "archived": True,
        }
