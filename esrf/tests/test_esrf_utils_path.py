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
import pprint
import unittest

from  esrf.utils.esrf_utils_path import UtilsPath

class Test(unittest.TestCase):


    def test_getMovieFileNameParametersFromMotioncorrPath(self):
        # Test 1
        mrcFullPath1 = "/mntdirect/_data_visitor/mx2006/cm01/20180123/PROCESSED_DATA/sa1mgml/saribs/Runs/000058_ProtMotionCorr/extra/GridSquare_22879601_Data_FoilHole_22888571_Data_22885672_22885673_20180124_0845-4482_aligned_mic.mrc"
        dictResult1 = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(mrcFullPath1)
        refDict1 = {'data': '_Data_',
 'date': '20180124',
 'directory': '/mntdirect/_data_visitor/mx2006/cm01/20180123/PROCESSED_DATA/sa1mgml/saribs/Runs/000058_ProtMotionCorr/extra',
 'extra': '_aligned_mic',
 'gridSquare': 'GridSquare_22879601',
 'hour': '0845',
 'id1': '22888571',
 'id2': '22885672',
 'id3': '22885673',
 'movieName': 'FoilHole_22888571_Data_22885672_22885673_20180124_0845-4482',
 'movieNumber': '4482',
 'prefix': 'FoilHole',
 'suffix': 'mrc'} 
        self.assertEqual(refDict1, dictResult1)
        # Test 2
        mrcFullPath2 = "/users/svensson/ScipionUserData/projects/TestPipeLine/Runs/000859_ProtMotionCorr/extra/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344_aligned_mic.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(mrcFullPath2)
        refDict2 = {'data': None,
 'date': '20170619',
 'directory': '/users/svensson/ScipionUserData/projects/TestPipeLine/Runs/000859_ProtMotionCorr/extra',
 'extra': '_aligned_mic',
 'gridSquare': None,
 'hour': '2101',
 'id1': '19150795',
 'id2': '19148847',
 'id3': '19148848',
 'movieName': 'FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344',
 'movieNumber': '0344',
 'prefix': 'FoilHole',
 'suffix': 'mrc'}
        self.assertEqual(refDict2, dictResult2)
        

    def test_getMovieFileNameParameters(self):
        # Test1
        movieFullPath1 = "/users/svensson/cryoem/CWAT_ESRF_RawData_K2/170619_bGal1/Images-Disc1/GridSquare_19141127/Data/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc"
        dictResult1 = UtilsPath.getMovieFileNameParameters(movieFullPath1)
        refDict1 = {'date': '20170619',
 'directory': '/users/svensson/cryoem/CWAT_ESRF_RawData_K2/170619_bGal1/Images-Disc1/GridSquare_19141127/Data',
 'extra': '',
 'gridSquare': 'GridSquare_19141127',
 'hour': '2101',
 'id1': '19150795',
 'id2': '19148847',
 'id3': '19148848',
 'movieName': 'FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344',
 'movieNumber': '0344',
 'prefix': 'FoilHole',
 'suffix': 'mrc'}
        self.assertEqual(refDict1, dictResult1)
        # Test 2
        mrcFullPath2 = "/data/visitor/mx415/cm01/20180315/RAW_DATA/EPU_BSA_grid5_2mg_2_test8/Images-Disc1/GridSquare_15806527/Data/FoilHole_15814308_Data_15808956_15808957_20180317_1109-17665.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParameters(mrcFullPath2)
        refDict2 = {'date': '20180317',
 'directory': '/data/visitor/mx415/cm01/20180315/RAW_DATA/EPU_BSA_grid5_2mg_2_test8/Images-Disc1/GridSquare_15806527/Data',
 'extra': '',
 'gridSquare': 'GridSquare_15806527',
 'hour': '1109',
 'id1': '15814308',
 'id2': '15808956',
 'id3': '15808957',
 'movieName': 'FoilHole_15814308_Data_15808956_15808957_20180317_1109-17665',
 'movieNumber': '17665',
 'prefix': 'FoilHole',
 'suffix': 'mrc'}
        self.assertEqual(refDict2, dictResult2)
        

    def test_getMovieJpegMrcXml(self):
        movieFullPath = "/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448-3385.mrc"
        jpeg, mrc, xml, gridSquareThumbNail =  UtilsPath.getMovieJpegMrcXml(movieFullPath)
        jpegRef = "/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.jpg"
        self.assertEqual(jpegRef, jpeg)
        mrcRef = "/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.mrc"
        self.assertEqual(mrcRef, mrc)
        xmlRef = "/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.xml"
        self.assertEqual(xmlRef, xml)
        gridSquareThumbNailRef = "/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/GridSquare_20171123_144119.jpg" 
        self.assertEqual(gridSquareThumbNailRef, gridSquareThumbNail)

 
    def test_getAlignMoviesPngLogFilePath(self):
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic.mrc"
        dictResult = UtilsPath.getAlignMoviesPngLogFilePath(mrcFilePath)
        dictRef = {'doseWeightMrc': '/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic_DW.mrc',
 'globalShiftPng': '/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_global_shifts.png',
 'logFileFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/logs/run.log',
 'thumbnailPng': '/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_thumbnail.png'}
        self.assertEqual(dictRef, dictResult)

        
    def test_getShiftData(self):
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic.mrc"
        dictResult = UtilsPath.getShiftData(mrcFilePath)
        dictRef = {'averageMotionPerFrame': 6.3, 'noPoints': 40, 'totalMotion': 250.6}
        self.assertEqual(dictRef, dictResult)

    def test_getXmlMetaData(self):
        xmlMetaDataFullPath = "/scisoft/pxsoft/data/cryoem/testMetaData/supervisor_20171115_150623/Images-Disc1/GridSquare_15441375/Data/FoilHole_15445484_Data_15444206_15444207_20171115_1620.xml"
        dictResult = UtilsPath.getXmlMetaData(xmlMetaDataFullPath)
        dictRef = {'accelerationVoltage': '300000',
 'acquisitionDateTime': '2017-11-15T16:20:52.2530023+01:00',
 'dose': '2.3276455783574426E+21',
 'nominalMagnification': '130000',
 'numberOffractions': '30',
 'phasePlateUsed': 'true',
 'positionX': '0.00026971729600000011',
 'positionY': '0.00014176793600000005',
 'superResolutionFactor': '1'}
        self.assertEqual(dictRef, dictResult)
    

    def test_getCtfMetaData(self):
        workingDir = "/scisoft/pxsoft/data/cryoem/testRunData/20171017/000977_ProtGctf"
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20171017/000859_ProtMotionCorr/extra/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344_aligned_mic.mrc"
        dictResult = UtilsPath.getCtfMetaData(workingDir, mrcFilePath)
        dictRef = {'Angle': '85.03',
 'CCC': '0.001368',
 'Defocus_U': '12558.52',
 'Defocus_V': '12380.92',
 'Phase_shift': None,
 'estimatedBfactor': '83.88',
 'logFilePath': '/scisoft/pxsoft/data/cryoem/testRunData/20171017/000977_ProtGctf/logs/run.log',
 'resolutionLimit': '3.839',
 'spectraImageFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20171017/000977_ProtGctf/extra/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344_aligned_mic/ctfEstimation.mrc',
 'spectraImageSnapshotFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20171017/000977_ProtGctf/extra/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344_aligned_mic/ctfEstimation.jpeg'}
        self.assertEqual(dictRef, dictResult)
        workingDir = "/scisoft/pxsoft/data/cryoem/testRunData/20171120/Runs/000117_ProtGctf"
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20171120/Runs/000056_ProtMotionCorr/extra/FoilHole_15445484_Data_15444206_15444207_20171115_1620-1324_aligned_mic.mrc"
        dictResult = UtilsPath.getCtfMetaData(workingDir, mrcFilePath)
        dictRef = {'Angle': '72.75',
 'CCC': '0.213712',
 'Defocus_U': '1977.10',
 'Defocus_V': '1991.74',
 'Phase_shift': '41.52',
 'estimatedBfactor': '271.93',
 'logFilePath': '/scisoft/pxsoft/data/cryoem/testRunData/20171120/Runs/000117_ProtGctf/logs/run.log',
 'resolutionLimit': '3.875',
 'spectraImageFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20171120/Runs/000117_ProtGctf/extra/FoilHole_15445484_Data_15444206_15444207_20171115_1620-1324_aligned_mic/ctfEstimation.mrc',
 'spectraImageSnapshotFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20171120/Runs/000117_ProtGctf/extra/FoilHole_15445484_Data_15444206_15444207_20171115_1620-1324_aligned_mic/ctfEstimation.jpeg'}

        self.assertEqual(dictRef, dictResult)
          
    def test_getPyarchFilePath(self):
        mrcFilePath = "/data/visitor/mx415/cm01/20171108/RAW_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198.mrc"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2017/cm01/mx415/20171108/RAW_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198.mrc", pyarchFilePath)
        mrcFilePath = "/mntdirect/_data_visitor/mx415/cm01/20171108/PROCESSED_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2017/cm01/mx415/20171108/PROCESSED_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc", pyarchFilePath)
        # ihls2975...
        mrcFilePath = "/mntdirect/_data_cm01_inhouse/Hons/IH-LS-2975/RAW_DATA/grid1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2018/cm01/ihls2975/Hons/RAW_DATA/grid1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc", pyarchFilePath)
        mrcFilePath = "/mntdirect/_data_cm01_inhouse/opcm01/20171108/RAW_DATA/nicetest/Frame.mrc"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2018/20171108/opcm01/RAW_DATA/nicetest/Frame.mrc", pyarchFilePath)

    def tes_copyToPyarchPath(self):
        # Can only be tested on a computer which can write to /data/pyarch
        testPath = "/data/visitor/mx415/cm01/20180101/RAW_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198.mrc"
        if not os.path.exists(os.path.dirname(testPath)):
            os.makedirs(testPath)
        if not os.path.exists(testPath):
            f = open(testPath)
            f.write("Test")
            f.close()
        pyarchFilePath = UtilsPath.getPyarchFilePath(testPath)
        print(pyarchFilePath)
        pyarchFilePath = UtilsPath.copyToPyarchPath(testPath)
        print(pyarchFilePath)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()