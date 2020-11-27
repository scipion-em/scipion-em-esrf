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

from  esrf.utils.esrf_utils_icat import UtilsIcat


class Test(unittest.TestCase):

    def tes_uploadToIcat(self):
        listFiles = [
            "/data/visitor/mx2005/cm01/20171209/RAW_DATA/" +
            "baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/" +
            "FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925.mrc"
        ]
        directory = \
            "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2"
        proposal = "id310009"
        sample = "sample1"
        dataSetName = "GridSquare_7259648_{0}".format(round(time.time()))
        dictMetadata = {"EM_amplitude_contrast": 0.0,
            "EM_dose_initial": 1.0,
            "EM_dose_per_frame": 2.0,
            "EM_images_count": 3.0,
            "EM_magnification": 4.0,
            "EM_position_x": 5.0,
            "EM_position_y": 6.0,
            "EM_protein_acronym": 7.0,
            "EM_sampling_rate": 8.0,
            "EM_spherical_aberration": 9.0,
            "EM_voltage": 10.0}
        UtilsIcat.uploadToIcat(
            listFiles, directory, proposal, sample, dataSetName, dictMetadata
        )

    def archiveGridSquare(self, proposal, sampleAcronym, allParams, gridSquareToBeArchived):
        # Archive remaining movies
        print("Archiving grid square: {0}".format(gridSquareToBeArchived))
        listPathsToBeArchived = []
        sumPositionX = 0.0
        sumPositionY = 0.0
        indexPosition = 0
        for movieName in allParams:
            if "gridSquare" in allParams[movieName] and allParams[movieName]["gridSquare"] == gridSquareToBeArchived and not allParams[movieName]["archived"]:
                listPathsToBeArchived.append(allParams[movieName]["movieFullPath"])
                allParams[movieName]["archived"] = True
                try:
                    sumPositionX += float(allParams[movieName]["positionX"])
                    sumPositionY += float(allParams[movieName]["positionY"])
                    indexPosition += 1
                except:
                    pass
        noImagesToBeArchived = len(listPathsToBeArchived)
        if noImagesToBeArchived > 0:
            if indexPosition > 0:
                meanPositionX = sumPositionX / indexPosition
                meanPositionY = sumPositionY / indexPosition
            else:
                meanPositionX = None
                meanPositionY = None
            dictIcatMetaData = dict(allParams["EM_meta_data"])
            dictIcatMetaData["EM_position_x"] = meanPositionX
            dictIcatMetaData["EM_position_y"] = meanPositionY
            directory = dictIcatMetaData["EM_directory"]
            listGalleryPath = allParams[gridSquareToBeArchived]["listGalleryPath"]
            dataSetName = "{0}_{1}".format(gridSquareToBeArchived, round(time.time()))
            allParams[dataSetName] = dictIcatMetaData
            print("listPathsToBeArchived: {0}".format(pprint.pformat(listPathsToBeArchived)))
            print("directory: {0}".format(directory))
            print("proposal: {0}".format(proposal))
            print("sampleAcronym: {0}".format(sampleAcronym))
            print("dataSetName: {0}".format(dataSetName))
            print("dictIcatMetaData: {0}".format(pprint.pformat(dictIcatMetaData)))
            errorMessage = UtilsIcat.uploadToIcat(listPathsToBeArchived, directory, proposal,
                                                  sampleAcronym, dataSetName, dictIcatMetaData,
                                                  listGalleryPath)
            if errorMessage is not None:
                print("ERROR during icat upload!")
                print(errorMessage)


    # def tes_archive_blc2531(self):
    #     proposal = "blc12531"
    #     sampleAcronym = "grid3"
    #     allParamsFile = "/data/cm01/commissioning/BLC12531/ApoF/20201118/PROCESSED_DATA/BLC12531-ApoF-19112020-grid3-EPU/allParams.json"
    #     with open(allParamsFile) as fd:
    #         allParams = json.loads(fd.read())
    #     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
    #     for gridSquareToBeArchived in dictGridSquares:
    #         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()