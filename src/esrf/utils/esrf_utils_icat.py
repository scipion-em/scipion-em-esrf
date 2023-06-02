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
import sys
import time
import traceback

from pyicat_plus.client.main import IcatClient
from esrf.utils.ESRFMetadataManagerClient import MetadataManagerClient
from esrf.utils.esrf_utils_path import UtilsPath


class UtilsIcat(object):
    @staticmethod
    def getDataFilesToBeArchived(allParams):
        listFiles = []
        return listFiles

    @staticmethod
    def uploadToIcat(
        listFiles,
        directory,
        proposal,
        sample,
        dataSetName,
        dictMetadata={},
        listGalleryPath=[],
    ):
        errorMessage = None
        try:
            os.environ["TANGO_HOST"] = "l-cryoem-1.esrf.fr:20000"
            metadataManagerName = "cm01/metadata/ingest"
            metaExperimentName = "cm01/metadata/experiment"
            client = MetadataManagerClient(metadataManagerName, metaExperimentName)
        except Exception:
            errorMessage = UtilsIcat.getStackTraceLog()

        if errorMessage is None:
            try:
                client.start(directory, proposal, sample, dataSetName)
            except Exception:
                errorMessage = UtilsIcat.getStackTraceLog()

        if errorMessage is None:
            try:
                for filePath in listFiles:
                    archivePath = filePath.replace(directory + "/", "")
                    client.appendFile(archivePath)
                dictMetadata["definition"] = "EM"
                for attributeName, value in dictMetadata.items():
                    setattr(client.metadataManager, attributeName, str(value))
            except Exception:
                errorMessage = UtilsIcat.getStackTraceLog()

        if errorMessage is None:
            try:
                galleryString = ""
                for galleryPath in listGalleryPath:
                    if galleryString == "":
                        galleryString = galleryPath
                    else:
                        galleryString += ", " + galleryPath
                if galleryString != "":
                    setattr(
                        client.metadataManager,
                        "ResourcesGalleryFilePaths",
                        galleryString,
                    )
            except Exception:
                print("ERROR when uploading gallery paths:")
                print(UtilsIcat.getStackTraceLog())

        if errorMessage is None:
            try:
                client.end()
            except Exception:
                errorMessage = UtilsIcat.getStackTraceLog()
        return errorMessage

    @staticmethod
    def findGridSquaresNotUploaded(allParams, gridSquareNotToArchive=None, timeout=900):
        listGridSquares = []
        for key, entry in allParams.items():
            if "archived" in entry and not entry["archived"]:
                if "gridSquare" in entry:
                    gridSquare = entry["gridSquare"]
                    if (
                        time.time() > allParams[gridSquare]["lastMovieTime"] + timeout
                        and gridSquare not in listGridSquares
                    ):
                        listGridSquares.append(gridSquare)
                elif "movieFullPath" in entry:
                    movieFullPath = entry["movieFullPath"]
                    dictFileNameParameters = (
                        UtilsPath.getEpuTiffMovieFileNameParameters(movieFullPath)
                    )
                    gridSquare = dictFileNameParameters["gridSquare"]
                    if gridSquare not in listGridSquares:
                        listGridSquares.append(gridSquare)
        return listGridSquares

    @staticmethod
    def getStackTraceLog():
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        errorMessage = "{0} {1}\n".format(exc_type, exc_value)
        listTrace = traceback.extract_tb(exc_traceback)
        for listLine in listTrace:
            errorMessage += '  File "%s", line %d, in %s%s\n' % (
                listLine[0],
                listLine[1],
                listLine[2],
                os.linesep,
            )
        return errorMessage

    # https://gitlab.esrf.fr/icat/hdf5-master-config/-/blob/master/hdf5_cfg.xml
    # <group NX_class="NXsubentry" groupName="EM">
    #    <protein_acronym ESRF_description="Protein acronym" NAPItype="NX_CHAR">${EM_protein_acronym}</protein_acronym>
    #    <voltage ESRF_description="Voltage" NAPItype="NX_CHAR">${EM_voltage}</voltage>
    #    <magnification ESRF_description="Magnification" NAPItype="NX_CHAR">${EM_magnification}</magnification>
    #    <images_count ESRF_description="Number of images in movie" NAPItype="NX_CHAR">${EM_images_count}</images_count>
    #    <position_x ESRF_description="Position X" NAPItype="NX_CHAR">${EM_position_x}</position_x>
    #    <position_y ESRF_description="Position Y" NAPItype="NX_CHAR">${EM_position_y}</position_y>
    #    <dose_initial ESRF_description="Dose initial" NAPItype="NX_CHAR">${EM_dose_initial}</dose_initial>
    #    <dose_per_frame ESRF_description="Dose per frame" NAPItype="NX_CHAR">${EM_dose_per_frame}</dose_per_frame>
    #    <spherical_aberration ESRF_description="Spherical aberration" NAPItype="NX_CHAR">${EM_spherical_aberration}</spherical_aberration>
    #    <amplitude_contrast ESRF_description="Amplitude contrast" NAPItype="NX_CHAR">${EM_amplitude_contrast}</amplitude_contrast>
    #    <sampling_rate ESRF_description="samplingRate" NAPItype="NX_CHAR">${EM_sampling_rate}</sampling_rate>
    #    <tilt_angle ESRF_description="tilt_angle" NAPItype="NX_CHAR">${EM_tilt_angle}</tilt_angle>
    #    <grid_name ESRF_description="grid_name" NAPItype="NX_CHAR">${EM_grid_name}</grid_name>
    #    <group NX_class="NXcollection" groupName="motioncorrection">
    #       <total_motion ESRF_description="Total motion of the sample" NAPItype="NX_CHAR">${EMMotionCorrection_total_motion}</total_motion>
    #       <average_motion ESRF_description="Average motion" NAPItype="NX_CHAR">${EMMotionCorrection_average_motion}</average_motion>
    #       <frame_range ESRF_description="Motion frame range" NAPItype="NX_CHAR">${EMMotionCorrection_frame_range}</frame_range>
    #       <frame_dose ESRF_description="Dose/frame" NAPItype="NX_CHAR">${EMMotionCorrection_frame_dose}</frame_dose>
    #       <total_dose ESRF_description="Total dose" NAPItype="NX_CHAR">${EMMotionCorrection_total_dose}</total_dose>
    #    </group>
    #    <group NX_class="NXcollection" groupName="ctf">
    #       <resolution_limit ESRF_description="Limit of the resolution" NAPItype="NX_CHAR">${EMCTF_resolution_limit}</resolution_limit>
    #       <correlation ESRF_description="" NAPItype="NX_CHAR">${EMCTF_correlation}</correlation>
    #       <defocus_u ESRF_description="" NAPItype="NX_CHAR">${EMCTF_defocus_u}</defocus_u>
    #       <defocus_v ESRF_description="" NAPItype="NX_CHAR">${EMCTF_defocus_v}</defocus_v>
    #       <angle ESRF_description="" NAPItype="NX_CHAR">${EMCTF_angle}</angle>
    #       <estimated_b_factor ESRF_description="" NAPItype="NX_CHAR">${EMCTF_estimated_b_factor}</estimated_b_factor>
    #    </group>
    # </group>

    @staticmethod
    def uploadRawToIcatPlus(directory, proposal, dataSetName, dictMetadata={}):
        # Hard-coded metadata-urls
        metadata_urls = ["bcu-mq-01.esrf.fr:61613", "bcu-mq-02.esrf.fr:61613"]
        client = IcatClient(metadata_urls=metadata_urls)
        client.store_dataset(
            beamline="CM01",
            proposal=proposal,
            dataset=dataSetName,
            path=directory,
            metadata=dictMetadata,
        )

    @staticmethod
    def uploadProcessedToIcatPlus(directory, proposal, dataSetName, dictMetadata, raw):
        # Hard-coded metadata-urls and proposal for tests
        metadata_urls = ["bcu-mq-01.esrf.fr:61613", "bcu-mq-02.esrf.fr:61613"]
        client = IcatClient(metadata_urls=metadata_urls)
        client.store_processed_data(
            beamline="CM01",
            proposal=proposal,
            dataset=dataSetName,
            path=directory,
            metadata=dictMetadata,
            raw=raw,
        )
