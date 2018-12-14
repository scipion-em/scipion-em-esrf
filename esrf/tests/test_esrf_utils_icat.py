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
import pprint
import unittest

from esrf.utils.esrf_utils_icat import UtilsIcat

class Test(unittest.TestCase):


    def test_findGridSquaresNotUploaded(self):
        allParams = json.loads(open("/scisoft/pxsoft/data/cryoem/testRunData/20180423/allParams.json").read())
        dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
        pprint.pprint(dictGridSquares)

    def test_findGridSquaresNotUploaded_2(self):
        allParams = json.loads(open("/scisoft/pxsoft/data/cryoem/testRunData/20181105/allParams.json").read())
        dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams, "GridSquare_32013107")
        pprint.pprint(dictGridSquares)

    def tes_getStackTraceLog(self):
        errorMessage = None
        try:
            print(1/0)
        except:
            errorMessage = UtilsIcat.getStackTraceLog()
        print(errorMessage)
        self.assertNotEquals(errorMessage, None)
        
    def tes_uploadToIcat(self):
        listFiles = ["/data/visitor/mx415/cm01/20180619/RAW_DATA/epu-grid2-ddw49-1_1/Images-Disc1/GridSquare_7728190/Data/FoilHole_7742940_Data_7738968_7738969_20180611_0959.mrc"]
        directory = "/data/visitor/mx415/cm01/20180619/RAW_DATA/epu-grid2-ddw49-1_1"
        proposal = "id000001"
        sample = "Test"
        dataSetName = "Test_1_1"
        dictMetadata = {"EM_voltage": "300000"}
        listGalleryPath = ["/data/visitor/mx415/cm01/20180619/RAW_DATA/epu-grid2-ddw49-1_1/Images-Disc1/GridSquare_7728190/GridSquare_20180608_164247.jpg"]
        errorMessage = UtilsIcat.uploadToIcat(listFiles, directory, proposal, sample, 
                                              dataSetName, dictMetadata, listGalleryPath)
        print(errorMessage)

    def tes_getOutOfStandbyState(self):
        metadataManagerName = 'cm01_test/metadata/ingest'
        metaExperimentName = 'cm01_test/metadata/experiment'
        os.environ["TANGO_HOST"] = "l-cryoem-2.esrf.fr:20000"
        from ESRFMetadataManagerClient import MetadataManagerClient
        proposal = "id000001"
        directory = "/data/visitor/mx415/cm01/20180619/RAW_DATA/epu-grid2-ddw49-1_1"
        sample = "Test"
        dataSetName = "Test_1"
        import PyTango
        metadataManager = PyTango.client.Device(metadataManagerName)
        metaExperiment = PyTango.client.Device(metaExperimentName)
        print("MetadataManager state: {0}".format(metadataManager.state()))
#        print([str(metadataManager.state())])
        # Abort any RUNNING scan
#        if str(metadataManager.state()) == "RUNNING":
#            metadataManager.AbortScan()
#            print("MetadataManager state: {0}".format(metadataManager.state()))
#        # Start new scan
#        metaExperiment.proposal = proposal
#        print("MetadataManager state: {0}".format(metadataManager.state()))
#        metaExperiment.dataRoot = directory
#        print("MetadataManager state: {0}".format(metadataManager.state()))
##        metaExperiment.sample = sample
##        print("MetadataManager state: {0}".format(metadataManager.state()))
#        metadataManager.scanName = dataSetName
#        print("MetadataManager state: {0}".format(metadataManager.state()))
#        # Start scan
#        metadataManager.StartScan()
#        print("MetadataManager state: {0}".format(metadataManager.state()))
        # Now try with other client
        client = MetadataManagerClient(metadataManagerName, metaExperimentName)
        client.start(directory, proposal, sample, dataSetName)
        client.printStatus()

        
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()