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
import pathlib
import re
import glob
import json
import math
import time
import shutil
import datetime
import traceback
import xml.etree.ElementTree


class UtilsPath(object):
    @staticmethod
    def getMovieJpegMrcXml(movieFilePath):
        gridSquareSnapshot = None
        dictFileName = UtilsPath.getMovieFileNameParameters(movieFilePath)
        filePrefix = "{directory}/{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}".format(
            **dictFileName
        )
        jpeg = filePrefix + ".jpg"
        if not os.path.exists(jpeg):
            jpeg = None
        mrc = filePrefix + ".mrc"
        if not os.path.exists(mrc):
            mrc = None
        xml = filePrefix + ".xml"
        if not os.path.exists(xml):
            xml = None
        gridSquareDir = os.path.dirname(os.path.dirname(movieFilePath))
        listSnapshot = glob.glob(os.path.join(gridSquareDir, "*.jpg"))
        if len(listSnapshot) > 0:
            gridSquareSnapshot = listSnapshot[-1]

        return jpeg, mrc, xml, gridSquareSnapshot

    @staticmethod
    def getEpuTiffMovieJpegMrcXml(movieFilePath):
        gridSquareSnapshot = None
        fileDir = os.path.dirname(movieFilePath)
        if os.path.exists(fileDir):
            # Patch provided by Sebastien 2018/02/09 for forcing NFS cache:
            # logger.debug("NFS cache clear, doing os.fstat on directory {0}".format(fileDir))
            fd = os.open(fileDir, os.O_DIRECTORY)
            statResult = os.fstat(fd)  # noqa F841
            os.close(fd)
        dictFileName = UtilsPath.getEpuTiffMovieFileNameParameters(movieFilePath)
        filePrefix = "{directory}/{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}".format(
            **dictFileName
        )
        jpeg = filePrefix + ".jpg"
        if not os.path.exists(jpeg):
            jpeg = None
        # Check if we have mrc micrograph
        microGraph = filePrefix + ".mrc"
        if not os.path.exists(microGraph):
            # Check if we have tiff micrograph
            microGraph = filePrefix + ".tiff"
            if not os.path.exists(microGraph):
                microGraph = None
        xml = filePrefix + ".xml"
        if not os.path.exists(xml):
            xml = None
        gridSquareDir = os.path.dirname(os.path.dirname(movieFilePath))
        listSnapshot = glob.glob(os.path.join(gridSquareDir, "*.jpg"))
        if len(listSnapshot) > 0:
            gridSquareSnapshot = listSnapshot[-1]

        return jpeg, microGraph, xml, gridSquareSnapshot

    @staticmethod
    def getSerialEMMovieJpegMdoc(topDir, movieFilePath):
        gridSquareSnapshot = None
        jpeg = None
        mdoc = movieFilePath + ".mdoc"
        if not os.path.exists(mdoc):
            mdoc = None
        return jpeg, mdoc, gridSquareSnapshot

    @staticmethod
    def getAlignMoviesPngLogFilePath(mrcFilePath):
        dictResult = {}
        # Locate png file in same directory
        mrcDirectory = os.path.dirname(mrcFilePath)
        dictMrcFile = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(
            mrcFilePath
        )
        mrcMovieNumber = dictMrcFile["movieNumber"]
        listPng = glob.glob(os.path.join(mrcDirectory, "*.png"))
        for pngFile in listPng:
            dictFileNameParameters = (
                UtilsPath.getMovieFileNameParametersFromMotioncorrPath(pngFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                dictFileNameParameters["extra"] == "_global_shifts"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["globalShiftPng"] = pngFile
            elif (
                dictFileNameParameters["extra"] == "_thumbnail"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["thumbnailPng"] = pngFile
        listMrc = glob.glob(os.path.join(mrcDirectory, "*.mrc"))
        for mrcFile in listMrc:
            dictFileNameParameters = (
                UtilsPath.getMovieFileNameParametersFromMotioncorrPath(mrcFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                "DW" in dictFileNameParameters["extra"]
                and mrcMovieNumber == movieNumber
            ):
                dictResult["doseWeightMrc"] = mrcFile
        # Find log file
        dictResult["logFileFullPath"] = os.path.join(
            os.path.dirname(mrcDirectory), "logs", "run.stdout"
        )
        return dictResult

    @staticmethod
    def getEpuTiffAlignMoviesPngLogFilePath(mrcFilePath):
        dictResult = {}
        # Locate png file in same directory
        mrcDirectory = os.path.dirname(mrcFilePath)
        dictMrcFile = UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(
            mrcFilePath
        )
        mrcMovieNumber = dictMrcFile["movieNumber"]
        listPng = glob.glob(os.path.join(mrcDirectory, "*.png"))
        for pngFile in listPng:
            dictFileNameParameters = (
                UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(pngFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                dictFileNameParameters["extra"] == "global_shifts"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["globalShiftPng"] = pngFile
            elif (
                dictFileNameParameters["extra"] == "thumbnail"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["thumbnailPng"] = pngFile
        listMrc = glob.glob(os.path.join(mrcDirectory, "*.mrc"))
        for mrcFile in listMrc:
            dictFileNameParameters = (
                UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(mrcFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                "DW" in dictFileNameParameters["extra"]
                and mrcMovieNumber == movieNumber
            ):
                dictResult["doseWeightMrc"] = mrcFile
        # Find log file
        dictResult["logFileFullPath"] = os.path.join(
            os.path.dirname(mrcDirectory), "logs", "run.stdout"
        )
        return dictResult

    @staticmethod
    def getSerialEMAlignMoviesPngLogFilePath(mrcFilePath):
        dictResult = {}
        # Locate png file in same directory
        mrcDirectory = os.path.dirname(mrcFilePath)
        dictMrcFile = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(
            mrcFilePath
        )
        mrcMovieNumber = dictMrcFile["movieNumber"]
        listPng = glob.glob(os.path.join(mrcDirectory, "*.png"))
        for pngFile in listPng:
            dictFileNameParameters = (
                UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(pngFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                dictFileNameParameters["extra"] == "global_shifts"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["globalShiftPng"] = pngFile
            elif (
                dictFileNameParameters["extra"] == "thumbnail"
                and mrcMovieNumber == movieNumber
            ):
                dictResult["thumbnailPng"] = pngFile
        listMrc = glob.glob(os.path.join(mrcDirectory, "*.mrc"))
        for mrcFile in listMrc:
            dictFileNameParameters = (
                UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(mrcFile)
            )
            movieNumber = dictFileNameParameters["movieNumber"]
            if (
                "DW" in dictFileNameParameters["extra"]
                and mrcMovieNumber == movieNumber
            ):
                dictResult["doseWeightMrc"] = mrcFile
        # Find log file
        dictResult["logFileFullPath"] = os.path.join(
            os.path.dirname(mrcDirectory), "logs", "run.stdout"
        )
        return dictResult

    @staticmethod
    def etree_to_dict(t):
        p = re.compile("^{(.*)}")
        m = p.match(t.tag)
        if m is not None:
            t.tag = t.tag[m.span()[1] :]
        listTmp = list(map(UtilsPath.etree_to_dict, t.getchildren()))
        if len(listTmp) > 0:
            d = {t.tag: listTmp}
        else:
            d = {t.tag: t.text}
        return d

    @staticmethod
    def get_recursively(search_dict, field):
        """
        Takes a dict with nested lists and dicts,
        and searches all dicts for a key of the field
        provided.
        See: https://stackoverflow.com/q/14962485
        """
        fields_found = []

        for key, value in search_dict.items():

            if key == field:
                fields_found.append(value)

            elif isinstance(value, dict):
                results = UtilsPath.get_recursively(value, field)
                for result in results:
                    fields_found.append(result)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        more_results = UtilsPath.get_recursively(item, field)
                        for another_result in more_results:
                            fields_found.append(another_result)

        return fields_found

    @staticmethod
    def getXmlMetaData(xmlMetaDataFullPath):
        root = xml.etree.ElementTree.parse(xmlMetaDataFullPath).getroot()
        dictXML = UtilsPath.etree_to_dict(root)
        dictResults = {
            "numberOffractions": UtilsPath.get_recursively(
                dictXML, "NumberOffractions"
            )[0],
            "magnification": UtilsPath.get_recursively(dictXML, "NominalMagnification")[
                0
            ],
            "positionX": UtilsPath.get_recursively(dictXML, "X")[0],
            "positionY": UtilsPath.get_recursively(dictXML, "Y")[0],
            "accelerationVoltage": UtilsPath.get_recursively(
                dictXML, "AccelerationVoltage"
            )[0],
            "acquisitionDateTime": UtilsPath.get_recursively(
                dictXML, "acquisitionDateTime"
            )[0],
        }
        listKeyValue = UtilsPath.get_recursively(dictXML, "KeyValueOfstringanyType")
        for dictKey, dictValue in listKeyValue:
            if dictKey["Key"] == "Dose":
                dictResults["dose"] = dictValue["Value"]
            if dictKey["Key"] == "PhasePlateUsed":
                dictResults["phasePlateUsed"] = dictValue["Value"]
        listKeyValue = UtilsPath.get_recursively(dictXML, "CameraSpecificInput")[0]
        # print(listKeyValue)
        for dictKeyValueOfstringanyType in listKeyValue:
            dictKey = dictKeyValueOfstringanyType["KeyValueOfstringanyType"][0]
            dictValue = dictKeyValueOfstringanyType["KeyValueOfstringanyType"][1]
            if dictKey["Key"] == "SuperResolutionFactor":
                dictResults["superResolutionFactor"] = dictValue["Value"]
        return dictResults

    @staticmethod
    def getMdocMetaData(mdocMetaDataFullPath):
        dictResults = {}
        with open(mdocMetaDataFullPath) as f:
            listLines = f.readlines()
        for line in listLines:
            if "=" in line:
                key, value = line.split("=")
                dictResults[key.strip()] = value.strip()
        return dictResults

    @staticmethod
    def _getKeyValue(root, key):
        value = None
        keyFound = False
        for child in root:
            for subChild in child:
                if subChild.tag.endswith("Key") and subChild.text == key:
                    keyFound = True
                if keyFound and subChild.tag.endswith("Value"):
                    value = subChild.text
                    keyFound = False
                    break
        return value

    @staticmethod
    def createSpectraImageSnapshot(extraDirectory, mrcFileBase):
        spectraImageSnapshotFullPath = None
        spectraImageFullPath = os.path.join(extraDirectory, mrcFileBase + "_ctf.mrc")
        if os.path.exists(spectraImageFullPath):
            spectraImageSnapshotFullPath = os.path.join(
                extraDirectory, mrcFileBase + "_ctf.jpeg"
            )
            os.system(
                "bimg {0} {1}".format(
                    spectraImageFullPath, spectraImageSnapshotFullPath
                )
            )
            if not os.path.exists(spectraImageSnapshotFullPath):
                spectraImageSnapshotFullPath = None
        return spectraImageFullPath, spectraImageSnapshotFullPath

    @staticmethod
    def getCtfMetaData(workingDir, mrcFilePath):
        dictResults = {
            "spectraImageSnapshotFullPath": None,
            "spectraImageFullPath": None,
            "Defocus_U": None,
            "Defocus_V": None,
            "Angle": None,
            "CCC": None,
            "Phase_shift": None,
            "resolutionLimit": None,
            "estimatedBfactor": None,
            "logFilePath": None,
        }
        # Find extra directory
        mrcFileBase = os.path.basename(mrcFilePath).split(".mrc")[0]
        extraDirectory = os.path.join(workingDir, "extra")
        if os.path.exists(extraDirectory):
            (
                spectraImageFullPath,
                spectraImageSnapshotFullPath,
            ) = UtilsPath.createSpectraImageSnapshot(extraDirectory, mrcFileBase)
            dictResults["spectraImageFullPath"] = spectraImageFullPath
            dictResults["spectraImageSnapshotFullPath"] = spectraImageSnapshotFullPath
            ctfEstimationPath = os.path.join(extraDirectory, mrcFileBase + "_ctf.log")
            if os.path.exists(ctfEstimationPath):
                f = open(ctfEstimationPath)
                lines = f.readlines()
                f.close()
                for index in range(len(lines)):
                    if "Final Values" in lines[index]:
                        listLabels = lines[index - 1].split()
                        listValues = lines[index].split()
                        for label, value in zip(listLabels, listValues):
                            dictResults[label] = value
                    elif "Resolution limit" in lines[index]:
                        listValues = lines[index].split()
                        dictResults["resolutionLimit"] = listValues[-1]
                    elif "Estimated Bfactor" in lines[index]:
                        listValues = lines[index].split()
                        dictResults["estimatedBfactor"] = listValues[-1]
        # Find log file
        logFilePath = os.path.join(workingDir, "logs", "run.stdout")
        if os.path.exists(logFilePath):
            dictResults["logFilePath"] = logFilePath
        return dictResults

    @staticmethod
    def getMovieFileNameParameters(mrcFilePath):
        """
        FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc
        """
        try:
            dictResult = {}
            dictResult["directory"] = os.path.dirname(mrcFilePath)
            p = re.compile(
                "^(.*)/(GridSquare_[0-9]*)/"
                + "Data/(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)"
                + "-([0-9]*)(_?.*)\.(.*)"
            )
            m = p.match(mrcFilePath)
            if m is not None:
                dictResult["gridSquare"] = m.group(2)
                dictResult["prefix"] = m.group(3)
                dictResult["id1"] = m.group(4)
                dictResult["id2"] = m.group(5)
                dictResult["id3"] = m.group(6)
                dictResult["date"] = m.group(7)
                dictResult["hour"] = m.group(8)
                dictResult["movieNumber"] = m.group(9)
                dictResult["extra"] = m.group(10)
                dictResult["suffix"] = m.group(11)
                dictResult[
                    "movieName"
                ] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}-{movieNumber}".format(
                    **dictResult
                )
            else:
                # Try without the GridSquare directory
                p = re.compile(
                    "^(.*)/(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)"
                    + "-([0-9]*)(_?.*)\.(.*)"
                )
                m = p.match(mrcFilePath)
                dictResult["gridSquare"] = None
                dictResult["prefix"] = m.group(2)
                dictResult["id1"] = m.group(3)
                dictResult["id2"] = m.group(4)
                dictResult["id3"] = m.group(5)
                dictResult["date"] = m.group(6)
                dictResult["hour"] = m.group(7)
                dictResult["movieNumber"] = m.group(8)
                dictResult["extra"] = m.group(9)
                dictResult["suffix"] = m.group(10)
                dictResult[
                    "movieName"
                ] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}-{movieNumber}".format(
                    **dictResult
                )
        except Exception as e:
            raise e
            dictResult = None
        # Check numbers
        if not dictResult["hour"].isdigit() or not dictResult["movieNumber"].isdigit():
            dictResult = None
        return dictResult

    @staticmethod
    def getEpuTiffMovieFileNameParameters(mrcFilePath):
        """
        FoilHole_10859740_Data_10853322_10853324_20210611_233928_fractions.tiff
        """
        try:
            # print(mrcFilePath)
            dictResult = {}
            dictResult["directory"] = os.path.dirname(mrcFilePath)
            p = re.compile(
                "^(.*)/(GridSquare_[0-9]*)/"
                + "Data/(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)"
                + "_fractions\.(.*)"
            )
            m = p.match(mrcFilePath)
            if m is not None:
                dictResult["gridSquare"] = m.group(2)
                dictResult["prefix"] = m.group(3)
                dictResult["id1"] = m.group(4)
                dictResult["id2"] = m.group(5)
                dictResult["id3"] = m.group(6)
                dictResult["date"] = m.group(7)
                dictResult["hour"] = m.group(8)
                dictResult["suffix"] = m.group(9)
        except Exception as e:
            raise e
            dictResult = None
        # Check numbers
        if not dictResult["hour"].isdigit():
            dictResult = None
        else:
            dictResult[
                "movieName"
            ] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}_fractions".format(
                **dictResult
            )
            dictResult["movieNumber"] = dictResult["date"][-2:] + dictResult["hour"]
        return dictResult

    @staticmethod
    def getSerialEMMovieFileNameParameters(topDir, tifFilePath):
        """
        /data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214/grid5/data/140/mx2214_140_00001.tif
        """
        movieFileName = os.path.basename(tifFilePath)
        dictResult = {}
        p = re.compile("^(.*)_([0-9]*).(.*)")
        m = p.match(movieFileName)
        dictResult["directory"] = os.path.dirname(tifFilePath)
        dictResult["prefix"] = m.group(1)
        dictResult["movieNumber"] = m.group(2)
        dictResult["suffix"] = m.group(3)
        # Check numbers
        if not dictResult["movieNumber"].isdigit():
            dictResult = None
        else:
            # Add parent directories to movieName
            listPath = os.path.dirname(tifFilePath).split(os.sep)
            listTopDir = topDir.split(os.sep)
            # Check the three last levels
            while listPath[-3:] != listTopDir[-3:]:
                parentDir = listPath.pop()
                dictResult["prefix"] = parentDir + "_" + dictResult["prefix"]
            dictResult["movieName"] = "{prefix}_{movieNumber}".format(**dictResult)
        return dictResult

    @staticmethod
    def getMovieFileNameParametersFromMotioncorrPath(mrcFilePath):
        """
        FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc
        """
        dictResult = {}
        p = re.compile(
            "^(.*)/(GridSquare_[0-9]*)*(_Data_)*(.*)_"
            + "([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)-([0-9]*)(_?.*)\.(.*)"
        )
        m = p.match(mrcFilePath)
        dictResult["directory"] = os.path.dirname(mrcFilePath)
        dictResult["gridSquare"] = m.group(2)
        dictResult["data"] = m.group(3)
        dictResult["prefix"] = m.group(4)
        dictResult["id1"] = m.group(5)
        dictResult["id2"] = m.group(6)
        dictResult["id3"] = m.group(7)
        dictResult["date"] = m.group(8)
        dictResult["hour"] = m.group(9)
        dictResult["movieNumber"] = m.group(10)
        dictResult["extra"] = m.group(11)
        dictResult["suffix"] = m.group(12)
        dictResult[
            "movieName"
        ] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}-{movieNumber}".format(
            **dictResult
        )
        return dictResult

    @staticmethod
    def getEpuTiffMovieFileNameParametersFromMotioncorrPath(mrcFilePath):
        """
        GridSquare_10847341_Data_FoilHole_10851620_Data_10853313_10853315_20210611_161457_fractions_aligned_mic.mrc
        """
        dictResult = {}
        p = re.compile(
            "^(.*)/Images-Disc(.*)_GridSquare_([0-9]*)_"
            + "Data_(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)"
            + "_fractions_(.*)\.(.*)"
        )
        m = p.match(mrcFilePath)
        if m is not None:
            dictResult["gridSquare"] = m.group(3)
            dictResult["prefix"] = m.group(4)
            dictResult["id1"] = m.group(5)
            dictResult["id2"] = m.group(6)
            dictResult["id3"] = m.group(7)
            dictResult["date"] = m.group(8)
            dictResult["hour"] = m.group(9)
            dictResult["extra"] = m.group(10)
            dictResult["suffix"] = m.group(11)
            dictResult[
                "movieName"
            ] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}_fractions".format(
                **dictResult
            )
            dictResult["movieNumber"] = dictResult["date"][-2:] + dictResult["hour"]
        return dictResult

    @staticmethod
    def getSerialEMMovieFileNameParametersFromMotioncorrPath(mrcFilePath):
        """
        000064_ProtMotionCorr/extra/grid5_data_140_mx2214_140_00001_aligned_mic.mrc
        """
        try:
            dictResult = {}
            p = re.compile("^(.*)/(.*)_([0-9]*)_(.*).(.*)")
            m = p.match(mrcFilePath)
            dictResult["directory"] = os.path.dirname(mrcFilePath)
            dictResult["prefix"] = m.group(2)
            dictResult["movieNumber"] = m.group(3)
            dictResult["extra"] = m.group(4)
            dictResult["suffix"] = m.group(5)
            dictResult["movieName"] = "{prefix}_{movieNumber}".format(**dictResult)
        except BaseException:
            dictResult = None
        # Check numbers
        if not dictResult["movieNumber"].isdigit():
            dictResult = None
        return dictResult

    @staticmethod
    def removeFileSystemPrefix(filePath):
        newFilePath = filePath
        for prefix in ["/gpfs/easy", "/gpfs/jazzy", "/gz", "hz"]:
            if filePath.startswith(prefix):
                newFilePath = filePath.replace(prefix, "")
                break
        return newFilePath

    @staticmethod
    def getPyarchFilePath(workingDir):
        """
        This method translates from a "visitor" path to a "pyarch" path:
        /data/visitor/mx415/id14eh1/20100209 -> /data/pyarch/2010/id14eh1/mx415/20100209
        """
        pyarchFilePath = None
        # Check problem of type /gpfs/easy
        directory = UtilsPath.removeFileSystemPrefix(workingDir)
        list_directory = directory.split(os.sep)
        list_beamline = ["cm01"]
        # Check that we have at least four levels of directories:
        if len(list_directory) > 5:
            topDirectory = list_directory[1]
            secondDirectory = list_directory[2]
            proposal = None
            beamline = None
            year = list_directory[5][0:4]
            # Check that we have a year that make sense...
            try:
                intYear = int(year)
                if intYear < 2017 and intYear > 2100:
                    # Something looks wrong, take the current year...
                    year = str(datetime.datetime.now().year)
            except BaseException:
                # Something looks wrong, take the current year...
                year = str(datetime.datetime.now().year)

            # Work around for ihls2975...
            if list_directory[4] == "IH-LS-2975":
                year = "2018"
                beamline = "cm01"
                proposal = "ihls2975"
                listOfRemainingDirectories = list_directory[5:]
                listOfRemainingDirectories.insert(0, list_directory[3])

            elif topDirectory == "mntdirect" and secondDirectory == "_data_visitor":
                proposal = list_directory[3]
                beamline = list_directory[4]
                listOfRemainingDirectories = list_directory[5:]

            elif topDirectory == "mnt" and secondDirectory == "multipath-shares":
                proposal = list_directory[5]
                beamline = list_directory[6]
                listOfRemainingDirectories = list_directory[7:]

            elif topDirectory == "mntdirect" and "_data_cm01_" in secondDirectory:

                if "inhouse" in secondDirectory:
                    proposal = list_directory[3]
                    beamline = list_directory[4]
                    listOfRemainingDirectories = list_directory[5:]
                else:
                    proposal = list_directory[3]
                    beamline = "cm01"
                    listOfRemainingDirectories = list_directory[4:]

            elif topDirectory == "data" and secondDirectory == "visitor":
                proposal = list_directory[3]
                beamline = list_directory[4]
                listOfRemainingDirectories = list_directory[5:]

            elif topDirectory == "data" and secondDirectory in list_beamline:
                beamline = secondDirectory
                proposal = list_directory[4]
                listOfRemainingDirectories = list_directory[5:]

            if (proposal is not None) and (beamline is not None):
                pyarchFilePath = os.path.join(os.sep, "data")
                pyarchFilePath = os.path.join(pyarchFilePath, "pyarch")
                pyarchFilePath = os.path.join(pyarchFilePath, year)
                pyarchFilePath = os.path.join(pyarchFilePath, beamline)
                pyarchFilePath = os.path.join(pyarchFilePath, proposal)
                for remainingDirectory in listOfRemainingDirectories:
                    pyarchFilePath = os.path.join(pyarchFilePath, remainingDirectory)

        if pyarchFilePath is None:
            print("ERROR! Directory path not converted for pyarch: %s" % directory)
        return pyarchFilePath

    @staticmethod
    def copyToPyarchPath(filePath):
        pyarchFilePath = None
        if filePath is not None and os.path.exists(filePath):
            try:
                # Check if we have a "standard" ESRF data path
                if "RAW_DATA" in filePath or "PROCESSED_DATA" in filePath:
                    pyarchFilePath = UtilsPath.getPyarchFilePath(filePath)
                    pyarchFileDir = os.path.dirname(pyarchFilePath)
                    if not os.path.exists(pyarchFileDir):
                        os.makedirs(pyarchFileDir, 0o755)
                    shutil.copy(filePath, pyarchFilePath)
                    os.chmod(pyarchFilePath, 0o644)
                else:
                    # Test path:
                    testPath = "/data/pyarch/2017/cm01/test"
                    # Add date
                    datePath = os.path.join(
                        testPath, time.strftime("%Y%m%d", time.localtime(time.time()))
                    )
                    # Loop until done
                    isDone = False
                    fileName = os.path.basename(filePath)
                    pyarchFilePath = None
                    while not isDone:
                        timePath = os.path.join(
                            datePath,
                            time.strftime("%H%M%S", time.localtime(time.time())),
                        )
                        if os.path.exists(timePath):
                            time.sleep(1)
                        else:
                            pyarchFilePath = os.path.join(timePath, fileName)
                            os.makedirs(timePath, 0o755)
                            shutil.copy(filePath, pyarchFilePath)
                            os.chmod(filePath, 0o644)
                            isDone = True
            except BaseException:
                print("ERROR uploading file {0} tp pyarch!".format(filePath))
                traceback.print_exc()
            if pyarchFilePath is None or not os.path.exists(pyarchFilePath):
                pyarchFilePath = filePath
        return pyarchFilePath

    @staticmethod
    def getShiftData(filePath):
        dictResults = {}
        logFile = os.path.join(
            os.path.dirname(os.path.dirname(filePath)), "logs", "run.stdout"
        )
        if os.path.exists(logFile):
            listLines = open(logFile).readlines()
            index = 0
            noPoints = 0
            # Look for mrc file
            mrcFileName = os.path.basename(filePath)
            foundMrc = False
            foundShiftTable = False
            listXShift = []
            listYShift = []
            totalMotion = 0.0
            while index < len(listLines):
                line = listLines[index]
                if mrcFileName in line:
                    foundMrc = True
                if foundMrc:
                    if "Full-frame alignment shift" in line:
                        foundShiftTable = True
                    elif foundShiftTable:
                        if len(line) > 1:
                            listLine = line.split()
                            try:
                                # print(listLine)
                                xShift = float(listLine[5])
                                yShift = float(listLine[6].strip())
                                listXShift.append(xShift)
                                listYShift.append(yShift)
                                totalMotion += math.sqrt(xShift ** 2 + yShift ** 2)
                                noPoints += 1
                            except BaseException:
                                pass
                        else:
                            foundShiftTable = False
                            foundMrc = False

                index += 1
            dictResults["noPoints"] = noPoints
            if totalMotion != 0:
                dictResults["totalMotion"] = round(totalMotion, 1)
                dictResults["averageMotionPerFrame"] = round(totalMotion / noPoints, 1)

        return dictResults

    @staticmethod
    def findSerialEMFilePaths(topDirectory):
        tifDir = None
        firstTifFileName = None
        defectFilePath = None
        dm4FilePath = None
        listTif = []
        for dirName, subdirList, fileList in os.walk(topDirectory, topdown=False):
            for fileName in fileList:
                if fileName.endswith(".tif"):
                    listTif.append(os.path.join(dirName, fileName))
        if len(listTif) > 0:
            listTif.sort()
            firstTifPath = listTif[0]
            tifDir = os.path.dirname(firstTifPath)
            firstTifFileName = os.path.basename(firstTifPath)
            listFiles = os.listdir(tifDir)
            for file in listFiles:
                if file.startswith("defect") and file.endswith(".txt"):
                    defectFilePath = os.path.join(tifDir, file)
                elif file.endswith(".dm4"):
                    dm4FilePath = os.path.join(tifDir, file)
        return tifDir, firstTifFileName, defectFilePath, dm4FilePath

    @staticmethod
    def serialEMFilesPattern(dataDirectory, tifDir):
        filesPattern = None
        lastDirName = os.path.basename(dataDirectory)

        listTifDir = tifDir.split(os.sep)
        filesPattern = ""
        for path in listTifDir[::-1]:
            if path == lastDirName:
                break
            else:
                filesPattern += "*/"
        filesPattern += "*.tif"
        return filesPattern

    @staticmethod
    def getBlacklist(listMovies, allParamsJsonFile):
        with open(allParamsJsonFile, "r") as f:
            dictAllParams = json.loads(f.read())
        dictGridSquare = {}
        # First find all grid squares which contain
        # movies that have not been processed
        for movie in listMovies:
            dictMovieName = UtilsPath.getEpuTiffMovieFileNameParameters(movie)
            gridSquare = dictMovieName["gridSquare"]
            if gridSquare not in dictGridSquare:
                dictGridSquare[gridSquare] = []
            movieName = os.path.splitext(os.path.basename(movie))[0]
            if movieName in dictAllParams.keys():
                dictMovie = dictAllParams[movieName]
                if "motionCorrectionId" in dictMovie:
                    if "CTFid" not in dictMovie:
                        dictGridSquare[gridSquare].append(movieName)
                else:
                    dictGridSquare[gridSquare].append(movieName)
            else:
                dictGridSquare[gridSquare].append(movieName)
        # Blacklist all grid squares with less than 50 movies
        blacklist = []
        for gridSquare in dictGridSquare.keys():
            if len(dictGridSquare[gridSquare]) < 25:
                blacklist.append("(.*){0}(.*)".format(gridSquare))
        return blacklist

    @staticmethod
    def getBlacklistAllMovies(listMovies, allParamsJsonFile):
        with open(allParamsJsonFile, "r") as f:
            dictAllParams = json.loads(f.read())
        blacklist = []
        for movie in listMovies:
            movieName = os.path.splitext(os.path.basename(movie))[0]
            if movieName in dictAllParams.keys():
                dictMovie = dictAllParams[movieName]
                if "motionCorrectionId" in dictMovie:
                    if "CTFid" in dictMovie:
                        blacklist.append(movie)
        return blacklist

    @staticmethod
    def getInputParticleDict(pathToInputParticlesStarFile, allParams):
        with open(pathToInputParticlesStarFile) as fd:
            listLines = fd.readlines()
        # Find the line which starts with " 1":
        indexStart = 0
        foundStart = False
        while not foundStart:
            line = listLines[indexStart]
            if len(line.split()) > 0 and line.split()[0] == "1":
                foundStart = True
                break
            else:
                indexStart += 1
        gridSquareMovieNameStart = listLines[indexStart].split()[3]
        # print(gridSquareMovieName)
        movieNameStart = gridSquareMovieNameStart[
            gridSquareMovieNameStart.find("_Data_") + 6 :
        ]
        movieNameStart = os.path.splitext(movieNameStart)[0]
        movieDictStart = allParams[movieNameStart]
        firstMovieFullPath = movieDictStart["movieFullPath"]
        # Find the last entry
        indexEnd = len(listLines) - 1
        foundEnd = False
        while not foundEnd:
            line = listLines[indexEnd]
            if len(line.split()) > 0:
                foundEnd = True
                break
            else:
                indexEnd -= 1
        numberOfParticles = listLines[indexEnd].split()[0]
        gridSquareMovieNameEnd = listLines[indexEnd].split()[3]
        movieNameEnd = gridSquareMovieNameEnd[
            gridSquareMovieNameEnd.find("_Data_") + 6 :
        ]
        movieNameEnd = os.path.splitext(movieNameEnd)[0]
        movieDictEnd = allParams[movieNameEnd]
        lastMovieFullPath = movieDictEnd["movieFullPath"]
        particleDict = {
            "firstMovieFullPath": firstMovieFullPath,
            "lastMovieFullPath": lastMovieFullPath,
            "numberOfParticles": numberOfParticles,
        }
        return particleDict

    @classmethod
    def parseRelionModelStarFile(cls, filePath):
        with open(filePath) as fd:
            lines = fd.readlines()
        lineIndex = 0
        found = False
        # Number of classes:
        while not found:
            line = lines[lineIndex]
            if line.startswith("_rlnNrClasses"):
                numberOfClasses = int(line.split()[1])
                found = True
            else:
                lineIndex += 1
        # Information per class
        found = False
        while not found:
            line = lines[lineIndex]
            if line.startswith("_rlnClassPriorOffsetY"):
                found = True
            lineIndex += 1
        listClass = []
        for index in range(numberOfClasses):
            line = lines[lineIndex]
            listLine = line.split()
            dictClass = {
                "index": index + 1,
                "referenceImage": listLine[0],
                "classDistribution": float(listLine[1]),
                "accuracyRotations": float(listLine[2]),
                "accuracyTranslationsAngst": float(listLine[3]),
                "estimatedResolution": float(listLine[4]),
                "overallFourierCompleteness": float(listLine[5]),
                "classPriorOffsetX": float(listLine[6]),
                "classPriorOffsetY": float(listLine[7]),
            }
            listClass.append(dictClass)
            lineIndex += 1
        dictStarFile = {"numberOfClasses": numberOfClasses, "classes": listClass}
        return dictStarFile

    @staticmethod
    def getTSFileParameters(file_path):
        extra = None
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        file_stem, suffix = os.path.splitext(file_name)
        list_file_name = file_stem.split("_")
        movie_name = "_".join(list_file_name[:8])
        ts_number = list_file_name[2]
        grid_name = list_file_name[0]
        movie_number = list_file_name[3]
        if list_file_name[1] != "Position" or \
            list_file_name[7] != "fractions":
            raise RuntimeError(f"ERROR! Path can not be parsed: {file_path}")
        if len(list_file_name) > 8:
            extra = "_".join(list_file_name[8:])
        # RAW_DATA or PROCESSED_DATA directory
        if "RAW_DATA" in directory:
            date_dir = directory.split("RAW_DATA")[0]
            icat_top_dir = os.path.join(date_dir, "RAW_DATA")
        elif "PROCESSED_DATA" in directory:
            date_dir = directory.split("PROCESSED_DATA")[0]
            icat_top_dir = os.path.join(date_dir, "PROCESSED_DATA")
        else:
            icat_top_dir = directory
        icat_dir = os.path.join(
            icat_top_dir,
            grid_name,
            f"{grid_name}_Position_{ts_number}",
            movie_number
        )
        raw_data_dir = os.path.join(date_dir, "RAW_DATA")
        dict_movie = {
            "file_path": str(file_path),
            "directory": str(directory),
            "file_name": file_name,
            "movie_name": movie_name,
            "grid_name": grid_name,
            "ts_number": int(ts_number),
            "movie_number": int(movie_number),
            "tilt_angle": float(list_file_name[4]),
            "date": list_file_name[5],
            "time": list_file_name[6],
            "extra": extra,
            "suffix": suffix,
            "icat_dir": icat_dir
        }
        return dict_movie

    @staticmethod
    def createIcatLink(file_path, icat_dir):
        file_name = file_path.name
        icat_path = icat_dir / file_name
        if icat_path.exists():
            raise RuntimeError(f"WARNING! File already archived: {icat_path}")
        else:
            os.symlink(str(file_path), str(icat_path))
            print(
                f"Created symlink : {file_path} -> {icat_path}"
            )
        return icat_path

    @staticmethod
    def createTiltSerieInstrumentSnapshot(icat_movie_path):
        if type(icat_movie_path) == str:
            icat_movie_path = pathlib.Path(icat_movie_path)
        if not icat_movie_path.exists():
            raise RuntimeError(f"File path {icat_movie_path} doesn't exist!")
        icat_dir = icat_movie_path.parent
        gallery_dir = icat_dir / "gallery"
        if not gallery_dir.exists():
            gallery_dir.mkdir(mode=0o755)
        temp_tif_path = gallery_dir / (icat_movie_path.stem + ".tif")
        snapshot_path = gallery_dir / (icat_movie_path.stem + ".jpg")
        os.system(f"bimg -average -truncate 0,1 -minmax 0,1 {icat_movie_path} {temp_tif_path}")
        os.system(f"bscale -bin 20 {temp_tif_path} {snapshot_path}")
        os.remove(str(temp_tif_path))

    @staticmethod
    def createTiltSerieSearchSnapshot(dict_movie, search_dir):
        movie_dir = pathlib.Path(dict_movie["directory"])
        grid_name = dict_movie["grid_name"]
        ts_number = dict_movie["ts_number"]
        if not movie_dir.exists():
            raise RuntimeError(f"File path {movie_dir} doesn't exist!")
        batch_dir = movie_dir / "Batch"
        grid_position = f"{grid_name}_Position_{ts_number}"
        search_file_name = grid_position + "_Search"
        search_mrc_path = batch_dir / (search_file_name + ".mrc")
        temp_tif_path = search_dir / (search_file_name + ".tif")
        search_snapshot_path = search_dir / (search_file_name + ".jpg")
        print("*"*80)
        print(str(search_mrc_path))
        print(str(search_snapshot_path))
        print("*" * 80)
        if search_mrc_path.exists():
            if not search_snapshot_path.exists():
                os.system(f"bimg -average -truncate 0,1 -minmax 0,1 {search_mrc_path} {temp_tif_path}")
                os.system(f"bscale -bin 6 {temp_tif_path} {search_snapshot_path}")
                os.remove(str(temp_tif_path))
        else:
            search_snapshot_path = None
        return search_snapshot_path