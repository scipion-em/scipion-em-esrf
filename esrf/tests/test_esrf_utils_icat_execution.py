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
import time
import unittest

from  esrf.utils.esrf_utils_icat import UtilsIcat

class Test(unittest.TestCase):


    def tes_uploadToIcat(self):
        listFiles = [
                    "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925.mrc",
                    ]
        directory = "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2"
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
        UtilsIcat.uploadToIcat(listFiles, directory, proposal, sample, dataSetName, dictMetadata)





if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()