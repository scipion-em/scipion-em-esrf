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

# Temporary hard-wired path for PyTango
sys.path.insert(0, "/opt/pxsoft/scipion/vESRF_dev/debian90-x86_64/scipion_dev/software/lib/python2.7/site-packages/pytango-9.2.0-py2.7-linux-x86_64.egg")
# import PyTango  # import isnt used in this file

from ESRFMetadataManagerClient import MetadataManagerClient

class UtilsIcat(object):
    

    @staticmethod
    def getDataFilesToBeArchived(allParams):
        listFiles = []
        return listFiles


    
    @staticmethod
    def uploadToIcat(listFiles, directory, proposal, sample, dataSetName, dictMetadata={}, listGalleryPath=[]):
        errorMessage = None
        try:
            os.environ["TANGO_HOST"] = "l-cryoem-2.esrf.fr:20000"
            metadataManagerName = 'cm01/metadata/ingest'
            metaExperimentName = 'cm01/metadata/experiment'
            client = MetadataManagerClient(metadataManagerName, metaExperimentName)
        except:
            errorMessage = UtilsIcat.getStackTraceLog()

        if errorMessage is None:
            try:
                client.start(directory, proposal, sample, dataSetName)
            except:
                errorMessage = UtilsIcat.getStackTraceLog()
                
        if errorMessage is None:
            try:
                for filePath in listFiles:
                    archivePath = filePath.replace(directory + "/", "")
                    client.appendFile(archivePath)
                dictMetadata["definition"] = "EM"
                for attributeName, value in dictMetadata.iteritems():
                    setattr(client.metadataManager, attributeName, str(value))
            except:
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
                    setattr(client.metadataManager, "ResourcesGalleryFilePaths", galleryString)
            except:
                print("ERROR when uploading gallery paths:")
                print(UtilsIcat.getStackTraceLog())

        if errorMessage is None:
            try:
                client.end()
            except:
                errorMessage = UtilsIcat.getStackTraceLog()
        return errorMessage

    @staticmethod
    def findGridSquaresNotUploaded(allParams, gridSquareNotToArchive=None):
        dictGridSquares = {}
        for key in allParams:
            entry = allParams[key]
            if "archived" in entry and not entry["archived"]:
                gridSquare = entry["gridSquare"]
                if gridSquare != gridSquareNotToArchive:
                    if not gridSquare in dictGridSquares:
                        dictGridSquares[gridSquare] = []
                    dictGridSquares[gridSquare].append(key)
        return dictGridSquares


    @staticmethod
    def getStackTraceLog():
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        errorMessage = "{0} {1}\n".format(exc_type, exc_value)
        listTrace = traceback.extract_tb(exc_traceback)
        for listLine in listTrace:
            errorMessage += "  File \"%s\", line %d, in %s%s\n" % (listLine[0], listLine[1], listLine[2], os.linesep)
        return errorMessage