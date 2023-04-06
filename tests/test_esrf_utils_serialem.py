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
import shutil
import tempfile
import unittest

from esrf.utils.esrf_utils_serialem import UtilsSerialEM


class Test(unittest.TestCase):
    def setUp(self):
        self.dataDir = (
            "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/"
            + "20190905/RAW_DATA/mx2214/data"
        )
        self.correctDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.correctDir)

    def test_createGainFile(self):
        dm4File = os.path.join(self.dataDir, "CountRef_mx2214_00005.dm4")
        gainPath = UtilsSerialEM.createGainFile(dm4File, self.correctDir)
        self.assertTrue(os.path.exists(gainPath))

    def test_createDefectMapFile(self):
        shiftFile = os.path.join(self.dataDir, "defects_bgal-215k-img-shift_0001.txt")
        tifFile = os.path.join(self.dataDir, "mx2214_00005.tif")
        defectMapPath = UtilsSerialEM.createDefectMapFile(
            shiftFile, tifFile, self.correctDir
        )
        self.assertTrue(os.path.exists(defectMapPath))
