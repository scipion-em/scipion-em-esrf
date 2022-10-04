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
import subprocess


class UtilsSerialEM(object):
    @staticmethod
    def createGainFile(dm4File, gainDir):
        fileName = os.path.splitext(os.path.basename(dm4File))[0]
        gainFilePath = os.path.join(gainDir, fileName + ".mrc")
        stdout = subprocess.check_output(["dm2mrc", dm4File, gainFilePath])
        print(stdout)
        return gainFilePath

    @staticmethod
    def createDefectMapFile(shiftFile, tifFile, gainDir):
        fileName = os.path.splitext(os.path.basename(shiftFile))[0]
        defectMapPath = os.path.join(gainDir, fileName + ".mrc")
        stdout = subprocess.check_output(
            ["clip", "defect", "-D", shiftFile, tifFile, defectMapPath]
        )
        print(stdout)
        return defectMapPath
