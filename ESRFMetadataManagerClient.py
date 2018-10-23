#!/usr/bin/env python
# coding: utf-8
# **************************************************************************
# *
# * Authors:     Alejandro de Maria (demariaa@esrf.fr) [1]
#                Olof Svensson (svensson@esrf.fr) [1]
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
"""A simple client for MetadataManager and MetaExperiment
"""

import os
import sys
import time
import logging
# Temporary hard-wired path for PyTango
sys.path.insert(0, "/opt/pxsoft/scipion/vESRF_dev/debian90-x86_64/scipion_dev/software/lib/python2.7/site-packages/pytango-9.2.0-py2.7-linux-x86_64.egg")
import PyTango.client
import traceback
from email.mime.text import MIMEText
import smtplib

class MetadataManagerClient(object):

    """
    A client for the MetadataManager and MetaExperiment tango Devices

    Attributes:
        name: name of the tango device. Example: 'id21/metadata/ingest'
    """

    def __init__(self, metadataManagerName, metaExperimentName):
        """
        Return a MetadataManagerClient object whose metadataManagerName is *metadataManagerName*
        and metaExperimentName is *metaExperimentName*
        """
        self.dataRoot = None
        self.proposal = None
        self.sample = None
        self.datasetName = None

        if metadataManagerName:
            self.metadataManagerName = metadataManagerName
        if metaExperimentName:
            self.metaExperimentName = metaExperimentName

        print('MetadataManager: %s' % metadataManagerName)
        print('MetaExperiment: %s' % metaExperimentName)

        # Tango Devices instances
        try:
            MetadataManagerClient.metadataManager = PyTango.client.Device(self.metadataManagerName)
            MetadataManagerClient.metaExperiment = PyTango.client.Device(self.metaExperimentName)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def printStatus(self):
        print('DataRoot: %s' % MetadataManagerClient.metaExperiment.dataRoot)
        print('Proposal: %s' % MetadataManagerClient.metaExperiment.proposal)
        print('Sample: %s' % MetadataManagerClient.metaExperiment.sample)
        print('Dataset: %s' % MetadataManagerClient.metadataManager.scanName)

    def getStatus(self):
        status = 'DataRoot: %s\n' % MetadataManagerClient.metaExperiment.dataRoot
        status += 'Proposal: %s\n' % MetadataManagerClient.metaExperiment.proposal
        status += 'Sample: %s\n' % MetadataManagerClient.metaExperiment.sample
        status += 'Dataset: %s\n' % MetadataManagerClient.metadataManager.scanName
        return status


    def __setDataRoot(self, dataRoot):
        try:
            MetadataManagerClient.metaExperiment.dataRoot = dataRoot
            self.dataRoot = dataRoot
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def __setProposal(self, proposal):
        """ Set proposal should be done before stting the data root """
        try:
            MetadataManagerClient.metaExperiment.proposal = proposal
            self.proposal = proposal
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def appendFile(self, filePath):
        try:
            MetadataManagerClient.metadataManager.lastDataFile = filePath
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def __setSample(self, sample):
        try:
            MetadataManagerClient.metaExperiment.sample = sample
            self.sample = sample
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def __setDataset(self, datasetName):
        try:
            MetadataManagerClient.metadataManager.scanName = datasetName
            self.datasetName = datasetName
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def start(self, dataRoot, proposal, sampleName, datasetName):
        """ Starts a new dataset """
        if MetadataManagerClient.metaExperiment:
            try:
                # setting proposal
                self.__setProposal(proposal)

                # setting dataRoot
                self.__setDataRoot(dataRoot)

                # setting sample
                self.__setSample(sampleName)

                # setting dataset
                self.__setDataset(datasetName)

                # setting datasetName
                if (str(MetadataManagerClient.metaExperiment.state()) == 'ON'):
                    if (str(MetadataManagerClient.metadataManager.state()) == 'ON'):
                        MetadataManagerClient.metadataManager.StartScan()

                # Give the server some time to react
                time.sleep(2)

            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise

    def end(self):
        try:
            MetadataManagerClient.metadataManager.endScan()
            # Give the server some time to react
            time.sleep(5)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def getState(self):
        return str(MetadataManagerClient.metadataManager.state())

    def getMessageList(self):
        return list(MetadataManagerClient.metadataManager.messageList)
    
    def abortScan(self):
        MetadataManagerClient.metadataManager.AbortScan()

            
if __name__ == '__main__':
    os.environ["TANGO_HOST"] = "l-cryoem-2.esrf.fr:20000"
    listFiles = [
                "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925.mrc",
                "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/process/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925_aligned_mic_DW.mrc",
                "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/process/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925_aligned_mic.mrc",
                "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/process/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925/run.log",
                "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/process/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925/ctfEstimation.mrc",
                          ]
    directory = "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2"
    proposal = "id310001"
    sample = "sample1"
    dataSetName = "GridSquare_7259648_{0}".format(round(time.time()))
    metadataManagerName = 'cm01/metadata/ingest'
    metaExperimentName = 'cm01/metadata/experiment'
    client = MetadataManagerClient(metadataManagerName, metaExperimentName)
    client.start(directory, proposal, sample, dataSetName)
    for filePath in listFiles:
        archivePath = filePath.replace(directory + "/", "")
        print(archivePath)
        client.appendFile(archivePath)
    dictMetadata = {"definition": "EM"}
    for attributeName, value in dictMetadata.iteritems():
        print("Setting metadata client attribute '{0}' to '{1}'".format(attributeName, value))
        setattr(client.metadataManager, attributeName, str(value))
    client.printStatus()
    client.end()


