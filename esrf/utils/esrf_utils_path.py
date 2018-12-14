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
import glob
import math
import time
import socket
import shutil
import datetime
import traceback
import xml.etree.ElementTree

class UtilsPath(object):
    
    
    @staticmethod
    def getMovieJpegMrcXml(movieFilePath):
        mrc = None
        xml = None
        gridSquareSnapshot = None
        dictFileName = UtilsPath.getMovieFileNameParameters(movieFilePath)
        filePrefix = "{directory}/{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}".format(**dictFileName)
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
    def getAlignMoviesPngLogFilePath(mrcFilePath):
        dictResult = {}
        # Locate png file in same directory
        mrcDirectory = os.path.dirname(mrcFilePath)
        dictMrcFile = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(mrcFilePath)
        mrcMovieNumber = dictMrcFile["movieNumber"]
        listPng = glob.glob(os.path.join(mrcDirectory, "*.png"))
        for pngFile in listPng:
            dictFileNameParameters = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(pngFile)
            movieNumber = dictFileNameParameters["movieNumber"]
            if dictFileNameParameters["extra"] == "_global_shifts" and mrcMovieNumber == movieNumber:
                dictResult["globalShiftPng"] = pngFile
            elif dictFileNameParameters["extra"] == "_thumbnail" and mrcMovieNumber == movieNumber:
                dictResult["thumbnailPng"] = pngFile
        listMrc = glob.glob(os.path.join(mrcDirectory, "*.mrc"))
        for mrcFile in listMrc:
            dictFileNameParameters = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(mrcFile)
            movieNumber = dictFileNameParameters["movieNumber"]
            if "DW" in dictFileNameParameters["extra"] and mrcMovieNumber == movieNumber:
                dictResult["doseWeightMrc"] = mrcFile            
        # Find log file
        dictResult["logFileFullPath"] = os.path.join(os.path.dirname(mrcDirectory), "logs", "run.log")
        return dictResult
    
    @staticmethod
    def etree_to_dict(t):
        p = re.compile("^\{(.*)\}")
        m = p.match(t.tag)
        if m is not None:
            t.tag = t.tag[m.span()[1]:]
        listTmp = map(UtilsPath.etree_to_dict, t.getchildren())
        if len(listTmp) > 0:
            d = {t.tag : listTmp}
        else:
            d = {t.tag : t.text}
        return d
 
    @staticmethod
    def get_recursively(search_dict, field):
        """
        Takes a dict with nested lists and dicts,
        and searches all dicts for a key of the field
        provided.
        See: https://stackoverflow.com/questions/14962485/finding-a-key-recursively-in-a-dictionary
        """
        fields_found = []
    
        for key, value in search_dict.iteritems():
    
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
        dictResults = {}
        root = xml.etree.ElementTree.parse(xmlMetaDataFullPath).getroot()
        dictXML = UtilsPath.etree_to_dict(root)
        listKeyValue = UtilsPath.get_recursively(dictXML, "KeyValueOfstringanyType")
        for dictKey, dictValue in listKeyValue:
            if dictKey["Key"] == "Dose":
                dictResults["dose"] = dictValue["Value"]
            if dictKey["Key"] == "PhasePlateUsed":
                dictResults["phasePlateUsed"] = dictValue["Value"]
        dictResults["numberOffractions"] = UtilsPath.get_recursively(dictXML, "NumberOffractions")[0]
        dictResults["nominalMagnification"] = UtilsPath.get_recursively(dictXML, "NominalMagnification")[0]
        dictResults["positionX"] = UtilsPath.get_recursively(dictXML, "X")[0]
        dictResults["positionY"] = UtilsPath.get_recursively(dictXML, "Y")[0]
        dictResults["accelerationVoltage"] = UtilsPath.get_recursively(dictXML, "AccelerationVoltage")[0]
        dictResults["acquisitionDateTime"] = UtilsPath.get_recursively(dictXML, "acquisitionDateTime")[0]
        listKeyValue = UtilsPath.get_recursively(dictXML, "CameraSpecificInput")[0]
        #print(listKeyValue)
        for dictKeyValueOfstringanyType in listKeyValue:
            dictKey = dictKeyValueOfstringanyType["KeyValueOfstringanyType"][0]
            dictValue = dictKeyValueOfstringanyType["KeyValueOfstringanyType"][1]
            if dictKey["Key"] == "SuperResolutionFactor":
                dictResults["superResolutionFactor"] = dictValue["Value"]
        #dictResults["superResolutionFactor"] = UtilsPath.get_recursively(dictXML, "superResolutionFactor")
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
        
    
    
    @ staticmethod
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
        # Find MRC directory
        mrcFileName = os.path.splitext(os.path.basename(mrcFilePath))[0]
        mrcDirectory = os.path.join(workingDir, "extra", mrcFileName)
        if os.path.exists(mrcDirectory):
            spectraImageFullPath = os.path.join(mrcDirectory, "ctfEstimation.mrc")
            if os.path.exists(spectraImageFullPath):
                dictResults["spectraImageFullPath"] = spectraImageFullPath
                spectraImageSnapshotFullPath = os.path.join(mrcDirectory, "ctfEstimation.jpeg")
                os.system("bimg {0} {1}".format(spectraImageFullPath, spectraImageSnapshotFullPath))
                if os.path.exists(spectraImageSnapshotFullPath):
                    dictResults["spectraImageSnapshotFullPath"] = spectraImageSnapshotFullPath
            ctfEstimationPath = os.path.join(mrcDirectory, "ctfEstimation.txt")
            if os.path.exists(ctfEstimationPath):
                f = open(ctfEstimationPath)
                lines = f.readlines()
                f.close()
                index = 0
                for index in range(len(lines)):
                    if "Final Values" in lines[index]:
                        listLabels = lines[index-1].split()
                        listValues = lines[index].split()
                        for label, value in zip(listLabels, listValues):
                            dictResults[label] = value
                    elif "Resolution limit" in lines[index]:
                        listValues = lines[index].split()
                        dictResults["resolutionLimit"] = listValues[-2]
                    elif "Estimated Bfactor" in lines[index]:
                        listValues = lines[index].split()
                        dictResults["estimatedBfactor"] = listValues[-2]
        # Find log file
        logFilePath = os.path.join(workingDir, "logs", "run.log")
        if os.path.exists(logFilePath):
            dictResults["logFilePath"] = logFilePath
        return dictResults

    @ staticmethod
    def getMovieFileNameParameters(mrcFilePath):
        """
        FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc
        """
        dictResult = {}
        p = re.compile("^(.*)/(GridSquare_[0-9]*)/Data/(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)-([0-9]*)(_?.*)\.(.*)")
        m = p.match(mrcFilePath)
        dictResult["directory"] = os.path.dirname(mrcFilePath)
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
        dictResult["movieName"] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}-{movieNumber}".format(**dictResult) 
        return dictResult

    @ staticmethod
    def getMovieFileNameParametersFromMotioncorrPath(mrcFilePath):
        """
        FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc
        """
        dictResult = {}
        p = re.compile("^(.*)/(GridSquare_[0-9]*)*(_Data_)*(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)-([0-9]*)(_?.*)\.(.*)")
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
        dictResult["movieName"] = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}-{movieNumber}".format(**dictResult) 
        return dictResult
    
    
    @ staticmethod
    def getPyarchFilePath(workingDir):
        """
        This method translates from a "visitor" path to a "pyarch" path:
        /data/visitor/mx415/id14eh1/20100209 -> /data/pyarch/2010/id14eh1/mx415/20100209
        """
        pyarchFilePath = None
        list_directory = workingDir.split(os.sep)
        list_beamline = ["cm01"]
        # Check that we have at least four levels of directories:
        if (len(list_directory) > 5):
            topDirectory = list_directory[ 1 ]
            secondDirectory = list_directory[ 2 ]
            proposal = None
            beamline = None
            year = list_directory[ 5 ][0:4]
            # Check that we have a year that make sense...
            try:
                intYear = int(year)
                if intYear < 2017 and intYear > 2100:
                    # Something looks wrong, take the current year...
                    year = str(datetime.datetime.now().year)
            except:
                # Something looks wrong, take the current year...
                year = str(datetime.datetime.now().year)
            
            # Work around for ihls2975...
            if list_directory[4] == "IH-LS-2975":
                year = "2018"
                beamline = "cm01"
                proposal = "ihls2975"
                listOfRemainingDirectories = list_directory[ 5: ]
                listOfRemainingDirectories.insert(0, list_directory[3])
              
            
            elif topDirectory == "mntdirect" and secondDirectory == "_data_visitor":
                proposal = list_directory[ 3 ]
                beamline = list_directory[ 4 ]
                listOfRemainingDirectories = list_directory[ 5: ]

            elif topDirectory == "mntdirect" and secondDirectory == "_data_cm01_inhouse":
                proposal = list_directory[ 3 ]
                beamline = list_directory[ 4 ]
                listOfRemainingDirectories = list_directory[ 5: ]
    
            elif topDirectory == "data" and secondDirectory == "visitor":
                proposal = list_directory[ 3 ]
                beamline = list_directory[ 4 ]
                listOfRemainingDirectories = list_directory[ 5: ]
    
            elif topDirectory == "data" and secondDirectory in list_beamline:
                beamline = secondDirectory
                proposal = list_directory[ 4 ]
                listOfRemainingDirectories = list_directory[ 5: ]
    
            if ((proposal != None) and
                (beamline != None)):
                pyarchFilePath = os.path.join(os.sep, "data")
                pyarchFilePath = os.path.join(pyarchFilePath, "pyarch")
                pyarchFilePath = os.path.join(pyarchFilePath, year)
                pyarchFilePath = os.path.join(pyarchFilePath, beamline)
                pyarchFilePath = os.path.join(pyarchFilePath, proposal)
                for directory in listOfRemainingDirectories:
                    pyarchFilePath = os.path.join(pyarchFilePath, directory)
    
        if (pyarchFilePath is None):
            print("ERROR! Directory path not converted for pyarch: %s" % workingDir)
        return pyarchFilePath

    @ staticmethod
    def copyToPyarchPath(filePath):
        pyarchFilePath = None
        if filePath is not None and os.path.exists(filePath):
            try:
                # Check if we have a "standard" ESRF data path
                if "RAW_DATA" in filePath or "PROCESSED_DATA" in filePath:
                    pyarchFilePath = UtilsPath.getPyarchFilePath(filePath)
                    pyarchFileDir = os.path.dirname(pyarchFilePath)
                    if not os.path.exists(pyarchFileDir):
                        os.makedirs(pyarchFileDir, 0755)
                    shutil.copy(filePath, pyarchFilePath)
                else:
                    # Test path:
                    testPath = "/data/pyarch/2017/cm01/test"
                    # Add date
                    datePath = os.path.join(testPath, time.strftime("%Y%m%d", time.localtime(time.time())))
                    # Loop until done
                    isDone = False
                    fileName = os.path.basename(filePath)
                    pyarchFilePath = None
                    while not isDone:
                        timePath = os.path.join(datePath, time.strftime("%H%M%S", time.localtime(time.time())))
                        if os.path.exists(timePath):
                            time.sleep(1)
                        else:
                            pyarchFilePath = os.path.join(timePath, fileName)
                            if "linsvensson" in socket.gethostname(): 
                                if os.path.getsize(filePath) < 1e6:
                                    # For the moment, only copy file if smaller than 1 MB
                                    os.system("ssh mxhpc2-1705 'mkdir -p {0}'".format(timePath))
                                    os.system("scp {0} mxhpc2-1705:{1}".format(filePath, pyarchFilePath))
                            else:
                                os.makedirs(timePath, 0755)
                                shutil.copy(filePath, pyarchFilePath)
                            isDone = True
            except:
                print("ERROR uploading file {0} tp pyarch!".format(filePath))
                traceback.print_exc()
            if pyarchFilePath is None or not os.path.exists(pyarchFilePath):
                pyarchFilePath = filePath
        return pyarchFilePath
        
                
    @ staticmethod
    def getShiftData(filePath):
        dictResults = {}
        logFile = os.path.join(os.path.dirname(os.path.dirname(filePath)), "logs", "run.stdout")
        if os.path.exists(logFile):
            listLines = open(logFile).readlines()
            index = 0
            noPoints = 0
            # Look for mrc file
            mrcFileName = os.path.basename(filePath)
            done = False
            foundMrc = False
            foundShiftTable = False
            listXShift = []
            listYShift = []
            totalMotion = 0.0
            while not done:
                line = listLines[index]
                if mrcFileName in line:
                    foundMrc = True
                if foundMrc:
                    if "Full-frame alignment shift" in line:
                        foundShiftTable = True
                    elif foundShiftTable:
                        #print(indexMrc, [line])
                        if len(line) > 1:
                            listLine = line.split()
                            #print(listLine)
                            xShift = float(listLine[5])
                            yShift = float(listLine[6].strip())
                            listXShift.append(xShift)
                            listYShift.append(yShift)
                            totalMotion += math.sqrt(xShift**2 + yShift**2)
                            noPoints += 1
                        else:
                            foundShiftTable = False
                            foundMrc = False
                    
                    
                index += 1
                if index >= len(listLines):
                    done = True
            dictResults["noPoints"] = noPoints
            dictResults["totalMotion"] = round(totalMotion, 1)
            dictResults["averageMotionPerFrame"] = round(totalMotion / noPoints, 1)
        return dictResults
 