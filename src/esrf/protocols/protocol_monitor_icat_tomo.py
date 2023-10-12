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
import time
import shutil
import pathlib
import threading
import collections

import pyworkflow.protocol.params as params

from pyworkflow import VERSION_1_1
from pyworkflow.protocol import getUpdatedProtocol
from emfacilities.protocols import ProtMonitor, Monitor, PrintNotifier
from pwem.protocols import ProtImportMovies, ProtCTFMicrographs
from motioncorr.protocols import ProtMotionCorr

from esrf.utils.esrf_utils_icat import UtilsIcat
from esrf.utils.esrf_utils_path import UtilsPath

# Debug possibility to turn off upload
DO_UPLOAD = True


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
            "sampleName",
            params.StringParam,
            default="unknown",
            label="Sample name",
            important=True,
            help="Name of the sample",
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
        self.sampleName = protocol.sampleName.get()
        self.movieDirectory = None
        self.current_dir = UtilsPath.removePrefixDirs(os.getcwd())
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
        self.no_ctf_threads = 0
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
        no_waiting = 0
        for movie_path in prot.getMatchFiles():
            movie_full_path = UtilsPath.removePrefixDirs(movie_path)
            dict_movie = UtilsPath.getTSFileParameters(movie_full_path)
            icat_raw_dir = pathlib.Path(dict_movie["icat_raw_dir"])
            movie_name = dict_movie["movie_name"]
            if movie_name not in self.all_params:
                if icat_raw_dir.exists():
                    self.info("Movie already archived: {0}".format(movie_name))
                elif self.no_movie_threads > 10:
                    no_waiting += 1
                    if no_waiting < 10:
                        self.info(
                            f"Waiting for movie threads... no_threads: {self.no_movie_threads}"
                        )
                else:
                    icat_raw_dir.mkdir(mode=0o755, exist_ok=False, parents=True)
                    # Check if we need to create search snapshot image
                    search_dir = icat_raw_dir.parent / "Search"
                    if not search_dir.exists():
                        search_dir.mkdir(mode=0o755, exist_ok=False)
                        search_path = UtilsPath.createTiltSerieSearchSnapshot(
                            dict_movie, search_dir
                        )
                        dict_movie["search_path"] = str(search_path)
                    # Start threads - if max number of threads not reached
                    self.no_movie_threads += 1
                    grid_name = self.sampleName
                    thread = threading.Thread(
                        target=self.archiveMovieInIcatPlus,
                        args=(prot, grid_name, movie_name, dict_movie, icat_raw_dir),
                    )
                    self.info(
                        f"Starting thread for movie {movie_name} - no_movie_threads: {self.no_movie_threads}"
                    )
                    thread.start()

    def uploadAlignMovies(self, prot):
        no_waiting = 0
        for micrograph in self.iter_updated_set(prot.outputMicrographs):
            micrograph_full_path = self.current_dir / micrograph.getFileName()
            dict_micrograph = UtilsPath.getTSFileParameters(micrograph_full_path)
            movie_name = dict_micrograph["movie_name"]
            if movie_name in self.all_params:
                dict_movie = self.all_params[movie_name]
                icat_mc_dir = (
                    pathlib.Path(dict_movie["icat_processed_dir"]) / "MotionCor"
                )
                if "mc_archived" not in dict_movie and "icat_raw_dir" in dict_movie:
                    if icat_mc_dir.exists():
                        self.info(
                            "Motion cor results already archived: {0}".format(
                                movie_name
                            )
                        )
                    elif self.no_mc_threads > 10:
                        no_waiting += 1
                        if no_waiting < 10:
                            self.info(
                                f"Waiting for mc threads... no_mc_threads: {self.no_mc_threads}"
                            )
                    else:
                        os.makedirs(icat_mc_dir, mode=0o755, exist_ok=False)
                        self.info(f"Archiving motion cor results {movie_name}")
                        # Start threads - if max number of threads not reached
                        self.no_mc_threads += 1
                        thread = threading.Thread(
                            target=self.archiveAlignedMovieInIcatPlus,
                            args=(prot, movie_name, micrograph_full_path, icat_mc_dir),
                        )
                        self.info(
                            f"Starting mc thread for movie {movie_name} - no_mc_threads: {self.no_mc_threads}"
                        )
                        thread.start()
                        # self.archiveAlignedMovieInIcatPlus(prot, movie_name, micrograph_full_path, icat_mc_dir)

    def uploadCTFMicrographs(self, prot):
        no_waiting = 0
        for ctf in self.iter_updated_set(prot.outputCTF):
            mc_full_path = self.current_dir / ctf.getMicrograph().getFileName()
            ctf_working_dir = self.current_dir / str(prot.workingDir)
            dict_micrograph = UtilsPath.getTSFileParameters(mc_full_path)
            movie_name = dict_micrograph["movie_name"]
            if movie_name in self.all_params:
                dict_movie = self.all_params[movie_name]
                icat_ctf_dir = pathlib.Path(dict_movie["icat_processed_dir"]) / "CTF"
                ctf_full_path = (
                    ctf_working_dir / "extra" / (movie_name + "_aligned_mic_DW_ctf.mrc")
                )
                if "ctf_archived" not in dict_movie and "icat_mc_dir" in dict_movie:
                    if os.path.exists(icat_ctf_dir):
                        self.info(
                            "CTF results already archived: {0}".format(movie_name)
                        )
                    elif self.no_ctf_threads > 10:
                        no_waiting += 1
                        if no_waiting < 10:
                            self.info(
                                f"Waiting for CTF threads... no_ctf_threads: {self.no_ctf_threads}"
                            )
                    else:
                        self.info(f"Archiving CTF results: {movie_name}")
                        os.makedirs(icat_ctf_dir, mode=0o755, exist_ok=False)
                        self.info(f"ctf_full_path: {ctf_full_path}")
                        self.no_ctf_threads += 1
                        thread = threading.Thread(
                            target=self.archiveCTFInIcatPlus,
                            args=(prot, movie_name, ctf_full_path, icat_ctf_dir),
                        )
                        self.info(
                            f"Starting ctf thread for movie {movie_name} - no_ctf_threads: {self.no_ctf_threads}"
                        )
                        thread.start()
                        # self.archiveCTFInIcatPlus(
                        #     prot, movie_name, ctf_full_path, icat_ctf_dir
                        # )

    def archiveMovieInIcatPlus(self, prot, grid_name, movie_name, dict_movie, icat_raw_dir):
        try:
            self.info(f"Archiving movie {movie_name}")
            self.all_params[movie_name] = dict_movie
            spherical_aberration = prot.sphericalAberration.get()
            amplitude_contrast = prot.amplitudeContrast.get()
            sampling_rate = prot.samplingRate.get()
            dose_initial = prot.doseInitial.get()
            dose_per_frame = prot.dosePerFrame.get()
            movie_full_path = pathlib.Path(dict_movie["file_path"])
            movie_number = dict_movie["movie_number"]
            tilt_angle = dict_movie["tilt_angle"]
            sample_name = dict_movie["sample_name"]
            icat_movie_path = UtilsPath.createIcatLink(movie_full_path, icat_raw_dir)
            UtilsPath.createTiltSerieInstrumentSnapshot(icat_movie_path)
            # Copy search snapshot to gallery
            if movie_number == 1 and "search_path" in dict_movie:
                shutil.copy(dict_movie["search_path"], icat_raw_dir / "gallery")
            self.info(f"Archiving movie: movie_full_path: {movie_full_path}")
            dictMetadata = {
                "Sample_name": sample_name,
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
            if DO_UPLOAD:
                time.sleep(5)
                UtilsIcat.uploadRawToIcatPlus(
                    directory=str(icat_raw_dir),
                    proposal=self.proposal,
                    dataSetName=f"{movie_number:03d}",
                    dictMetadata=dictMetadata,
                )
            self.all_params[movie_name]["raw_movie_archived"] = True
            self.all_params[movie_name]["icat_raw_dir"] = str(icat_raw_dir)
            self.info(
                f"Thread finished for movie {movie_name}, no_movie_threads: {self.no_movie_threads}"
            )
        except Exception as e:
            self.info("Error in ICAT upload:")
            self.info(e)
            (exc_type, exc_value, exc_traceback) = sys.exc_info()
            error_message = f"{exc_type} {exc_value}"
            self.info(error_message)
            list_trace = traceback.extract_tb(exc_traceback)
            self.info("Traceback (most recent call last): %s" % os.linesep)
            for list_line in list_trace:
                error_line = f"  File '{list_line[0]}', line {list_line[1]}, in {list_line[2]}{os.sep}"
                self.info(error_line)
            self.info(
                f"Thread finished with errors for movie {movie_name}, no_movie_threads: {self.no_movie_threads}"
            )
        self.no_movie_threads -= 1

    def archiveAlignedMovieInIcatPlus(
        self, prot, movie_name, micrograph_full_path, icat_mc_dir
    ):
        dict_movie = self.all_params[movie_name]
        sample_name = dict_movie["sample_name"]
        movie_number = dict_movie["movie_number"]
        icat_raw_dir = dict_movie["icat_raw_dir"]
        # Link "raw" data
        icat_mc_path = UtilsPath.createIcatLink(micrograph_full_path, icat_mc_dir)
        # Create snapshot image
        mc_galley_path = icat_mc_dir / "gallery"
        mc_galley_path.mkdir(mode=0o755)
        temp_tif_path = mc_galley_path / (micrograph_full_path.stem + ".tif")
        mc_snapshot_path = mc_galley_path / (micrograph_full_path.stem + ".jpg")
        os.system(f"/cvmfs/sb.esrf.fr/bin/bimg {micrograph_full_path} {temp_tif_path}")
        os.system(f"/cvmfs/sb.esrf.fr/bin/bscale -bin 12 {temp_tif_path} {mc_snapshot_path}")
        os.chmod(mc_snapshot_path, mode=0o644)
        os.remove(str(temp_tif_path))
        # Copy global shift snap shot
        drift_plot_full_path = micrograph_full_path.parent / (
            movie_name + "_global_shifts.png"
        )
        self.info(drift_plot_full_path)
        icat_drift_plot_path = mc_galley_path / drift_plot_full_path.name
        shutil.copy(drift_plot_full_path, icat_drift_plot_path)
        os.chmod(icat_drift_plot_path, 0o644)
        # Get metadata
        dict_shift_data = UtilsPath.getShiftData(micrograph_full_path)
        total_motion = dict_shift_data.get("totalMotion", None)
        average_motion = dict_shift_data.get("averageMotionPerFrame", None)
        frame_range = dict_shift_data.get("noPoints", None)
        dictMetadata = {
            "Sample_name": sample_name,
            "EMMotionCorrection_total_motion": total_motion,
            "EMMotionCorrection_average_motion": average_motion,
            "EMMotionCorrection_frame_range": frame_range,
            "EMMotionCorrection_frame_dose": -1.0,
            "EMMotionCorrection_total_dose": -1.0,
        }
        if DO_UPLOAD:
            time.sleep(5)
            UtilsIcat.uploadProcessedToIcatPlus(
                directory=str(icat_mc_dir),
                proposal=self.proposal,
                dataSetName=f"{movie_number:03d}_MotionCor",
                dictMetadata=dictMetadata,
                raw=[icat_raw_dir],
            )
        self.all_params[movie_name]["mc_archived"] = True
        self.all_params[movie_name]["icat_mc_path"] = str(icat_mc_path)
        self.all_params[movie_name]["icat_mc_dir"] = str(icat_mc_dir)
        self.no_mc_threads -= 1
        self.info(
            f"MC thread finished for movie {movie_name}, no_mc_threads: {self.no_mc_threads}"
        )

    def archiveCTFInIcatPlus(self, prot, movie_name, ctf_full_path, icat_ctf_dir):
        dict_movie = self.all_params[movie_name]
        sample_name = dict_movie["sample_name"]
        movie_number = dict_movie["movie_number"]
        movie_name = dict_movie["movie_name"]
        icat_mc_dir = dict_movie["icat_mc_dir"]
        # Read meta data
        working_dir = self.current_dir / str(prot.workingDir)
        ctf_dict_results = UtilsPath.getTSCtfMetaData(working_dir, movie_name)
        resolution_limit = ctf_dict_results.get("resolutionLimit", None)
        correlation = ctf_dict_results.get("CCC", None)
        defocus_u = ctf_dict_results.get("Defocus_U", None)
        defocus_v = ctf_dict_results.get("Defocus_V", None)
        angle = ctf_dict_results.get("Angle", None)
        estimated_b_factor = ctf_dict_results.get("estimatedBfactor", None)
        # Link "raw" data
        icat_ctf_path = UtilsPath.createIcatLink(ctf_full_path, icat_ctf_dir)
        # Create CTF snapshot image
        ctf_galley_path = icat_ctf_dir / "gallery"
        ctf_galley_path.mkdir(mode=0o755)
        mc_snapshot_path = ctf_galley_path / (ctf_full_path.stem + ".jpg")
        os.system(f"/cvmfs/sb.esrf.fr/bin/bimg -minmax 0,300 {ctf_full_path} {mc_snapshot_path}")
        dict_metadata = {
            "Sample_name": sample_name,
            "EMCTF_resolution_limit": resolution_limit,
            "EMCTF_correlation": correlation,
            "EMCTF_defocus_u": defocus_u,
            "EMCTF_defocus_v": defocus_v,
            "EMCTF_angle": angle,
            "EMCTF_estimated_b_factor": estimated_b_factor,
        }
        if DO_UPLOAD:
            time.sleep(5)
            UtilsIcat.uploadProcessedToIcatPlus(
                directory=str(icat_ctf_dir),
                proposal=self.proposal,
                dataSetName=f"{movie_number:03d}_CTF",
                dictMetadata=dict_metadata,
                raw=[icat_mc_dir],
            )
        self.all_params[movie_name]["ctf_archived"] = True
        self.all_params[movie_name]["icat_ctf_path"] = str(icat_ctf_path)
        self.all_params[movie_name]["icat_ctf_dir"] = str(icat_ctf_dir)
        self.no_ctf_threads -= 1
        self.info(
            f"CTF thread finished for movie {movie_name}, no_ctf_threads: {self.no_ctf_threads}"
        )
