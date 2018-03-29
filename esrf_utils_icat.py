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

from ESRFMetadataManagerClient import MetadataManagerClient

class UtilsIcat(object):
    

    @staticmethod
    def getDataFilesToBeArchived(allParams):
        listFiles = []
        return listFiles


    
    @staticmethod
    def uploadToIcat(listFiles, directory, proposal, sample, dataSetName, dictMetadata={}):
        os.environ["TANGO_HOST"] = "l-cryoem-2.esrf.fr:20000"
        metadataManagerName = 'cm01/metadata/ingest'
        metaExperimentName = 'cm01/metadata/experiment'
        client = MetadataManagerClient(metadataManagerName, metaExperimentName)
        client.start(directory, proposal, sample, dataSetName)
        for filePath in listFiles:
            archivePath = filePath.replace(directory + "/", "")
            client.appendFile(archivePath)
        dictMetadata["definition"] = "EM"
        for attributeName, value in dictMetadata.iteritems():
            setattr(client.metadataManager, attributeName, str(value))
        client.end() 