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
import pprint
import shutil
import threading
import collections
import time

import pyworkflow.protocol.params as params

from pyworkflow import VERSION_1_1
from pyworkflow.protocol import getUpdatedProtocol
from emfacilities.protocols import ProtMonitor, Monitor, PrintNotifier
from pwem.protocols import ProtImportMovies, ProtCTFMicrographs
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
            "all_params_json_file",
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
            samplingInterval=10,  # 30 seconds                                        # samplingInterval=self.samplingInterval.get(),
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
        self.current_dir = pathlib.Path(os.getcwd())
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
        self.no_movie_threads = 0
        self.no_mc_threads = 0
        if hasattr(protocol, "all_params_json_file"):
            self.all_params_json_file = protocol.all_params_json_file.get()
            if os.path.exists(self.all_params_json_file):
                try:
                    dictall_params = json.loads(open(self.all_params_json_file).read())
                    self.all_params = collections.OrderedDict(dictall_params)
                except BaseException:
                    self.all_params = collections.OrderedDict()
            else:
                self.all_params = collections.OrderedDict()
        else:
            self.all_params_json_file = None
            self.all_params = collections.OrderedDict()

    def step(self):
        self.info("MonitorISPyB: start step ------------------------")
        self.info("Number of movies in all params: {0}".format(len(self.all_params)))

        # Check if we should archive gain an defect maps
        # self.archiveGainAndDefectMap()

        if self.proposal == "None":
            self.info("WARNING! Proposal is 'None', no data uploaded to ICAT")
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
                elif isinstance(prot, ProtCTFMicrographs) and hasattr(
                    prot, "outputCTF"
                ):
                    self.uploadCTFMicrographs(prot)
                    isActiveCTFMicrographs = prot.isActive()
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
        if self.all_params_json_file is not None:
            thread = threading.Thread(
                target=self.noInterrupt,
                args=(self.all_params_json_file, json.dumps(self.all_params, indent=4)),
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
        # for movie in prot.iterNewInputFiles():
        #     movie_full_path = pathlib.Path(
        #         os.path.join(self.currentDir, movie.getFileName())
            # )
            dict_movie = UtilsPath.getTSFileParameters(movie_full_path)
            icat_dir = pathlib.Path(dict_movie["icat_dir"])
            movie_name = dict_movie["movie_name"]
            if movie_name not in self.all_params:
                self.all_params[movie_name] = dict_movie
                if icat_dir.exists():
                    self.info("Movie already archived: {0}".format(movie_name))
                else:
                    self.info(f"Archiving movie {movie_name}")
                    icat_dir.mkdir(mode=0o755, exist_ok=False, parents=True)
                    # Check if we need to create search snapshot image
                    search_dir = icat_dir.parent / "Search"
                    search_dir.mkdir(mode=0o755, exist_ok=True)
                    search_path = UtilsPath.createTiltSerieSearchSnapshot(dict_movie, search_dir)
                    dict_movie["search_path"] = str(search_path)
                    # Start threads - if max number of threads not reached
                    self.no_movie_threads += 1
                    while self.no_movie_threads > 10:
                        self.info(f"Waiting for threads... no_threads: {self.no_movie_threads}")
                        time.sleep(5)
                    thread = threading.Thread(
                        target=self.archiveMovieInIcatPlus,
                        args=(prot, movie_name, icat_dir)
                    )
                    self.info(f"Starting thread for movie {movie_name} - no_threads: {self.no_movie_threads}")
                    thread.start()
                    # self.archiveMovieInIcatPlus(prot, movie_name, icat_dir)

    def uploadAlignMovies(self, prot):
        for micrograph in self.iter_updated_set(prot.outputMicrographs):
            micrograph_full_path = self.current_dir / micrograph.getFileName()
            dict_micrograph = UtilsPath.getTSFileParameters(micrograph_full_path)
            mc_icat_dir = pathlib.Path(dict_micrograph["icat_dir"]) / "MotionCor"
            movie_name = dict_micrograph["movie_name"]
            if movie_name in self.all_params:
                dict_movie = self.all_params[movie_name]
                if "mc_archived" not in dict_movie and "icat_raw_path" in dict_movie:
                    if mc_icat_dir.exists():
                        self.info("Motion cor results already archived: {0}".format(movie_name))
                    else:
                        os.makedirs(mc_icat_dir, mode=0o755, exist_ok=False)
                        self.info(f"Archiving motion cor results {movie_name}")
                        # Start threads - if max number of threads not reached
                        self.no_mc_threads += 1
                        while self.no_mc_threads > 10:
                            self.info(f"Waiting for threads... no_threads: {self.no_mc_threads}")
                            time.sleep(5)
                        thread = threading.Thread(
                            target=self.archiveAlignedMovieInIcatPlus,
                            args=(prot, movie_name, micrograph_full_path, mc_icat_dir)
                        )
                        self.info(f"Starting mc thread for movie {movie_name} - no_threads: {self.no_mc_threads}")
                        thread.start()
                        # self.archiveAlignedMovieInIcatPlus(prot, movie_name, micrograph_full_path, mc_icat_dir)

    def uploadCTFMicrographs(self, prot):
        for ctf in self.iter_updated_set(prot.outputCTF):
            mc_full_path = self.current_dir / ctf.getMicrograph().getFileName()
            ctf_working_dir = self.current_dir / str(prot.workingDir)
            dict_movie = UtilsPath.getTSFileParameters(mc_full_path)
            movie_name = dict_movie["movie_name"]
            ctf_full_path = ctf_working_dir / "extra" / (mc_full_path.stem + "_ctf.mrc")
            ctf_icat_dir = pathlib.Path(dict_movie["icat_dir"]) / "CTF"
            if movie_name in self.all_params:
                dict_movie = self.all_params[movie_name]
                if "ctf_archived" not in dict_movie and "icat_mc_path" in dict_movie:
                    if os.path.exists(ctf_icat_dir):
                        self.info("CTF results already archived: {0}".format(movie_name))
                    else:
                        self.info(f"Archiving CTF results: {movie_name}")
                        os.makedirs(ctf_icat_dir, mode=0o755, exist_ok=False)
                        self.info(f"ctf_full_path: {ctf_full_path}")
                        self.archiveCTFInIcatPlus(prot, movie_name, ctf_full_path, ctf_icat_dir)

            # movie_name = micrograph_full_path.stem.split("_aligned_mic")[0]
            # if (
            #     movie_name in self.all_params
            #     and "motionCorrectionIcatPath" not in self.all_params[movie_name]
            # ):
            #     self.info("Motion corr movie name: {0}".format(movie_name))
            #     dict_movie = self.all_params[movie_name]
            #     movie_full_path = dict_movie["movie_full_path"]
            #     grid_name = dict_movie["grid_name"]
            #     ts_dir_name = dict_movie["ts_dir_name"]
            #     ts_movie_dir_name = dict_movie["ts_movie_dir_name"]
            #     self.info(
            #         "Align movies: movie {0}".format(os.path.basename(movie_full_path))
            #     )
            #     drift_plot_full_path = micrograph_full_path.parent / (
            #         movie_name + "_global_shifts.png"
            #     )
            #     self.info(drift_plot_full_path)
            #     corrected_dose_micrograph_full_path = micrograph_full_path.parent / (
            #         micrograph_full_path.stem + "_DW.mrc"
            #     )
            #     self.info(corrected_dose_micrograph_full_path)
            #     micrograph_snapshot_full_path = micrograph_full_path.parent / (
            #         movie_name + "_thumbnail.png"
            #     )
            #     self.info(micrograph_snapshot_full_path)
            #     if "PROCESSED_DATA" in self.currentDir:
            #         processed_data_dir = pathlib.Path(
            #             self.currentDir.split("PROCESSED_DATA")[0]
            #         )
            #     else:
            #         processed_data_dir = pathlib.Path(self.currentDir)
            #     processed_data_dir = processed_data_dir / "PROCESSED_DATA"
            #     icat_mc_cor_dir = (
            #         processed_data_dir / grid_name / ts_dir_name / ts_movie_dir_name
            #     )
            #     icat_mc_gallery_dir = icat_mc_cor_dir / "gallery"
            #     icat_mc_gallery_dir.mkdir(mode=0o755, exist_ok=True, parents=True)
            #     if drift_plot_full_path.exists():
            #         shutil.copy(str(drift_plot_full_path), str(icat_mc_gallery_dir))
                # dictShift = UtilsPath.getShiftData(micrograph_full_path)
                # if "totalMotion" in dictShift:
                #     totalMotion = dictShift["totalMotion"]
                # else:
                #     totalMotion = None
                # if "averageMotionPerFrame" in dictShift:
                #     averageMotionPerFrame = dictShift["averageMotionPerFrame"]
                # else:
                #     averageMotionPerFrame = None
                # logFileFullPath = dict_result["logFileFullPath"]
                # firstFrame = self.alignFrame0
                # lastFrame = self.alignFrameN
                # dosePerFrame = self.all_params[movie_name]["dosePerFrame"]
                # doseWeight = None
                # driftPlotPyarchPath = UtilsPath.copyToPyarchPath(driftPlotFullPath)
                # micrographPyarchPath = None
                # correctedDoseMicrographPyarchPath = None
                # micrographSnapshotPyarchPath = UtilsPath.copyToPyarchPath(
                #     micrographSnapshotFullPath
                # )
                # logFilePyarchPath = UtilsPath.copyToPyarchPath(logFileFullPath)

                # if self.all_params[movieName]["processDir"] is not None:
                #     shutil.copy(
                #         micrographFullPath, self.all_params[movieName]["processDir"]
                #     )
                #     shutil.copy(
                #         correctedDoseMicrographFullPath,
                #         self.all_params[movieName]["processDir"],
                #     )
                #     if os.path.exists(logFileFullPath):
                #         shutil.copy(
                #             logFileFullPath, self.all_params[movieName]["processDir"]
                #         )
                # noTrialsLeft = 5
                # uploadSucceeded = False
                # while not uploadSucceeded:
                #     motionCorrectionObject = None
                #     try:
                #         motionCorrectionObject = self.client.service.addMotionCorrection(
                #             proposal=self.proposal,
                #             movieFullPath=movieFullPath,
                #             firstFrame=firstFrame,
                #             lastFrame=lastFrame,
                #             dosePerFrame=dosePerFrame,
                #             doseWeight=doseWeight,
                #             totalMotion=totalMotion,
                #             averageMotionPerFrame=averageMotionPerFrame,
                #             driftPlotFullPath=driftPlotPyarchPath,
                #             micrographFullPath=micrographPyarchPath,
                #             correctedDoseMicrographFullPath=correctedDoseMicrographPyarchPath,
                #             micrographSnapshotFullPath=micrographSnapshotPyarchPath,
                #             logFileFullPath=logFilePyarchPath,
                #         )
                #     except Exception as e:
                #         self.info("Error when trying to upload motion correction!")
                #         self.info(e)
                #         motionCorrectionObject = None
                #     if motionCorrectionObject is not None:
                #         uploadSucceeded = True
                #         motionCorrectionId = motionCorrectionObject.motionCorrectionId
                #     else:
                #         if noTrialsLeft == 0:
                #             raise RuntimeError(
                #                 "ERROR: failure when trying to upload motion correction!"
                #             )
                #         else:
                #             self.info("ERROR! motionCorrectionObject is None!")
                #             self.info(
                #                 "Sleeping 5 s, and then trying again. Number of trials left: {0}".format(
                #                     noTrialsLeft
                #                 )
                #             )
                #             time.sleep(5)
                #             noTrialsLeft -= 1
                # time.sleep(0.1)
                # self.all_params[movieName]["motionCorrectionId"] = motionCorrectionId
                # self.all_params[movieName]["totalMotion"] = totalMotion
                # self.all_params[movieName][
                #     "averageMotionPerFrame"
                # ] = averageMotionPerFrame
                # self.updateJsonFile()
                #
                # self.protocol.info(
                #     "Upload of align movie results done, motionCorrectionId = {0}".format(
                #         motionCorrectionId
                #     )
                # )

    def archiveMovieInIcatPlus(self, prot, movie_name, icat_dir):
        spherical_aberration = prot.sphericalAberration.get()
        amplitude_contrast = prot.amplitudeContrast.get()
        sampling_rate = prot.samplingRate.get()
        dose_initial = prot.doseInitial.get()
        dose_per_frame = prot.dosePerFrame.get()
        dict_movie = self.all_params[movie_name]
        movie_full_path = pathlib.Path(dict_movie["file_path"])
        movie_number = dict_movie["movie_number"]
        grid_name = dict_movie["grid_name"]
        tilt_angle = dict_movie["tilt_angle"]
        ts_number = dict_movie["ts_number"]
        icat_movie_path = UtilsPath.createIcatLink(movie_full_path, icat_dir)
        UtilsPath.createTiltSerieInstrumentSnapshot(icat_movie_path)
        # Copy search snapshot to gallery
        shutil.copy(dict_movie["search_path"], icat_dir / "gallery")
        self.info(f"Archiving movie: movie_full_path: {movie_full_path}")
        dictMetadata = {
            "Sample_name": f"{grid_name}_Position_{ts_number}",
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
            "EM_tilt_angle": tilt_angle,
        }
        UtilsIcat.uploadToIcatPlus(
            directory=str(icat_dir),
            proposal=self.proposal,
            dataSetName=f"{movie_number:03d}",
            dictMetadata=dictMetadata
        )
        self.all_params[movie_name]["raw_movie_archived"] = True
        self.all_params[movie_name]["icat_raw_path"] = str(icat_movie_path)
        self.no_movie_threads -= 1
        self.info(f"Thread finished for movie {movie_name}")

    def archiveAlignedMovieInIcatPlus(self, prot, movie_name, micrograph_full_path, mc_icat_dir):
        dict_movie = self.all_params[movie_name]
        grid_name = dict_movie["grid_name"]
        ts_number = dict_movie["ts_number"]
        movie_number = dict_movie["movie_number"]
        icat_raw_path = dict_movie["icat_raw_path"]
        # Link "raw" data
        icat_mc_path = UtilsPath.createIcatLink(micrograph_full_path, mc_icat_dir)
        # Create snapshot image
        mc_galley_path = mc_icat_dir / "gallery"
        mc_galley_path.mkdir(mode=0o755)
        temp_tif_path = mc_galley_path / (micrograph_full_path.stem + ".tif")
        mc_snapshot_path = mc_galley_path / (micrograph_full_path.stem + ".jpg")
        os.system(f"bimg {micrograph_full_path} {temp_tif_path}")
        os.system(f"bscale -bin 12 {temp_tif_path} {mc_snapshot_path}")
        os.remove(str(temp_tif_path))
        # Copy global shift snap shot
        drift_plot_full_path = micrograph_full_path.parent / (
                movie_name + "_global_shifts.png"
        )
        self.info(drift_plot_full_path)
        shutil.copy(drift_plot_full_path, mc_galley_path)
        dictMetadata = {
            "Sample_name": f"{grid_name}_Position_{ts_number}",
            "raw": icat_raw_path,
            "EMMotionCorrection_total_motion": 0.0,
            "EMMotionCorrection_average_motion": 0.0,
            "EMMotionCorrection_frame_range": 0.0,
            "EMMotionCorrection_frame_dose": 0.0,
            "EMMotionCorrection_total_dose": 0.0,
        }
        UtilsIcat.uploadToIcatPlus(
            directory=str(mc_icat_dir),
            proposal=self.proposal,
            dataSetName=f"{movie_number:03d}",
            dictMetadata=dictMetadata
        )
        self.all_params[movie_name]["mc_archived"] = True
        self.all_params[movie_name]["icat_mc_path"] = str(icat_mc_path)
        self.no_mc_threads -= 1


    def archiveCTFInIcatPlus(self, prot, movie_name, ctf_full_path, ctf_icat_dir):
        dict_movie = self.all_params[movie_name]
        grid_name = dict_movie["grid_name"]
        ts_number = dict_movie["ts_number"]
        movie_number = dict_movie["movie_number"]
        icat_mc_path = dict_movie["icat_mc_path"]
        # Read meta data
        working_dir = self.current_dir / str(prot.workingDir)
        # ctf_dict_results = UtilsPath.getCtfMetaData(working_dir, ctf_full_path)
        # Link "raw" data
        icat_ctf_path = UtilsPath.createIcatLink(ctf_full_path, ctf_icat_dir)
        # Create CTF snapshot image
        ctf_galley_path = ctf_icat_dir / "gallery"
        ctf_galley_path.mkdir(mode=0o755)
        temp_tif_path = ctf_galley_path / (ctf_full_path.stem + ".tif")
        mc_snapshot_path = ctf_galley_path / (ctf_full_path.stem + ".jpg")
        os.system(f"bimg {ctf_full_path} {mc_snapshot_path}")
        dict_metadata = {
            "Sample_name": f"{grid_name}_Position_{ts_number}",
            "raw": icat_mc_path,
            "EMCTF_resolution_limit": 0.0,
            "EMCTF_correlation": 0.0,
            "EMCTF_defocus_u": 0.0,
            "EMCTF_defocus_v": 0.0,
            "EMCTF_angle": 0.0,
            "EMCTF_estimated_b_factor": 0.0,
        }
        UtilsIcat.uploadToIcatPlus(
            directory=str(ctf_icat_dir),
            proposal=self.proposal,
            dataSetName=f"{movie_number:03d}",
            dictMetadata=dict_metadata
        )
        self.all_params[movie_name]["ctf_archived"] = True
        self.all_params[movie_name]["icat_ctf_path"] = str(ctf_icat_dir)
