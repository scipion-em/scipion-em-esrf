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
        
    def test_getSerialEMMovieFileNameParametersFromMotioncorrPath(self):
        # Test 1
        mrcFullPath1 = "/mntdirect/_data_visitor/mx415/cm01/20191029/PROCESSED_DATA/mx2214/mx2214_20191029-110718/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic.mrc"
        dictResult1 = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(mrcFullPath1)
        refDict1 = {
            'directory': '/mntdirect/_data_visitor/mx415/cm01/20191029/PROCESSED_DATA/mx2214/mx2214_20191029-110718/Runs/000064_ProtMotionCorr/extra',
             'movieName': 'data_mx2214_00005',
             'movieNumber': '00005',
             'prefix': 'data_mx2214',
             'suffix': 'mrc',
             'extra': 'aligned_mic'
        }
        self.assertEqual(refDict1, dictResult1)
        # Test 2
        mrcFullPath2 = "/data/visitor/mx2112/cm01/20191029/PROCESSED_DATA/mx2214_1/mx2214_1_20191029-134731/Runs/000064_ProtMotionCorr/extra/grid5_data_140_mx2214_140_00001_aligned_mic.mrc"
        dictResult2 = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(mrcFullPath2)
        refDict2 = {
            'directory': '/data/visitor/mx2112/cm01/20191029/PROCESSED_DATA/mx2214_1/mx2214_1_20191029-134731/Runs/000064_ProtMotionCorr/extra',
             'movieName': 'grid5_data_140_mx2214_140_00001',
             'movieNumber': '00001',
             'prefix': 'grid5_data_140_mx2214_140',
             'suffix': 'mrc',
             'extra': 'aligned_mic'
        }
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
        # Test 3 - CRYOEM-33
        mrcFullPath2 = "/data/cm01/cmihr3/IH-LS3226/20191004/RAW_DATA/epu-grid4/Images-Disc1/GridSquare_3931883/Data/FoilHole_3936249_Data_3945596_3945597_20191004_1443-gain-ref.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParameters(mrcFullPath2)
        refDict2 = None
        self.assertEqual(refDict2, dictResult2)


    def test_getSerialEMMovieFileNameParameters(self):
        # Test1
        topDir1 = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        movieFullPath1 = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data/mx2214_00005.tif"
        dictResult1 = UtilsPath.getSerialEMMovieFileNameParameters(topDir1, movieFullPath1)
        refDict1 = {'directory': '/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data',
                    'movieName': 'data_mx2214_00005',
                    'movieNumber': '00005',
                    'prefix': 'data_mx2214',
                    'suffix': 'tif'}
        self.assertEqual(refDict1, dictResult1)
        # Test2
        topDir2 = "/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214"
        movieFullPath2 = "/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214/grid5/data/140/mx2214_140_00001.tif"
        dictResult2 = UtilsPath.getSerialEMMovieFileNameParameters(topDir2, movieFullPath2)
        refDict2 = {'directory': '/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214/grid5/data/140',
                    'movieName': 'grid5_data_140_mx2214_140_00001',
                    'movieNumber': '00001',
                    'prefix': 'grid5_data_140_mx2214_140',
                    'suffix': 'tif'}
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

    def test_getSerialEMAlignMoviesPngLogFilePath(self):
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic.mrc"
        dictResult = UtilsPath.getSerialEMAlignMoviesPngLogFilePath(mrcFilePath)
        dictRef = {
            'doseWeightMrc': '/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic_DW.mrc',
            'globalShiftPng': '/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_global_shifts.png',
            'logFileFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/logs/run.log',
            'thumbnailPng': '/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_thumbnail.png'}
        self.assertEqual(dictRef, dictResult)

    def test_getShiftData(self):
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic.mrc"
        dictResult = UtilsPath.getShiftData(mrcFilePath)
        dictRef = {'averageMotionPerFrame': 6.3, 'noPoints': 40, 'totalMotion': 250.6}
        self.assertEqual(dictRef, dictResult)

    def test_getXmlMetaData(self):
        xmlMetaDataFullPath = "/scisoft/pxsoft/data/cryoem/testMetaData/supervisor_20171115_150623/Images-Disc1/GridSquare_15441375/Data/FoilHole_15445484_Data_15444206_15444207_20171115_1620.xml"
        dictResult = UtilsPath.getXmlMetaData(xmlMetaDataFullPath)
        dictRef = {
            'accelerationVoltage': '300000',
            'acquisitionDateTime': '2017-11-15T16:20:52.2530023+01:00',
            'dose': '2.3276455783574426E+21',
            'nominalMagnification': '130000',
            'numberOffractions': '30',
            'phasePlateUsed': 'true',
            'positionX': '0.00026971729600000011',
            'positionY': '0.00014176793600000005',
            'superResolutionFactor': '1'
        }
        self.assertEqual(dictRef, dictResult)

    def test_getMdocMetaData(self):
        mdocMetaDataFullPath = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data/mx2214_00005.tif.mdoc"
        dictResult = UtilsPath.getMdocMetaData(mdocMetaDataFullPath)
        import pprint
        pprint.pprint(dictResult)
        dictRef = {
            'Binning': '1',
            'CameraIndex': '1',
            'CountsPerElectron': '1',
            'DateTime': '05-Sep-19  15:52:08',
            'DefectFile': 'defects_bgal-215k-img-shift_0001.txt',
            'Defocus': '0.0853802',
            'DividedBy2': '0',
            'ExposureDose': '0',
            'ExposureTime': '6',
            'FilterSlitAndLoss': '20 0',
            'FrameDosesAndNumber': '0 40',
            'GainReference': 'CountRef_mx2214_00005.dm4',
            'ImageShift': '-0.643144 -0.233229',
            'Intensity': '0.116205',
            'MagIndex': '32',
            'Magnification': '130000',
            'MultishotHoleAndPosition': '1 1',
            'NavigatorLabel': '78-1',
            'NumSubFrames': '40',
            'OperatingMode': '1',
            'PixelSpacing': '1.082',
            'RotationAngle': '174.52',
            'SpotSize': '6',
            'StagePosition': '-62.6189 730.271',
            'StageZ': '-32.565',
            'SubFramePath': 'X:\\DoseFractions\\mx2214\\data\\mx2214_00005.tif',
            'T': 'SerialEM: Acquired on Titan Krios D3693                 05-Sep-19  11:24:48',
            'TargetDefocus': '-2.6',
            'TiltAngle': '0.00577417',
            'Voltage': '300',
            '[FrameSet': '0]'
        }
        self.assertEqual(dictRef, dictResult)

    def test_getCtfMetaData(self):
        workingDir = "/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf"
        mrcFilePath = "/scisoft/pxsoft/data/cryoem/testRunData/20190715/000064_ProtMotionCorr/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic.mrc"
        dictResult = UtilsPath.getCtfMetaData(workingDir, mrcFilePath)
        dictRef = {'Angle': '35.60',
 'CCC': '-0.076290',
 'Defocus_U': '23173.92',
 'Defocus_V': '22988.54',
 'Phase_shift': None,
 'estimatedBfactor': '82.54',
 'logFilePath': '/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/logs/run.log',
 'resolutionLimit': '3.381',
 'spectraImageFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.mrc',
 'spectraImageSnapshotFullPath': '/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.jpeg'}
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
        self.assertEqual("/data/pyarch/2020/20171108/opcm01/RAW_DATA/nicetest/Frame.mrc", pyarchFilePath)
        # CRYOEM-25 : New paths for inhouse research...
        mrcFilePath = "/data/cm01/cmihr2/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087556/Data/FoilHole_4118111_Data_5127341_5127342_20181205_1023.jpg"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2018/cm01/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087556/Data/FoilHole_4118111_Data_5127341_5127342_20181205_1023.jpg", pyarchFilePath)
        mrcFilePath = "/mntdirect/_data_cm01_cmihr2/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087308/GridSquare_20181204_115820.jpg"
        pyarchFilePath = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual("/data/pyarch/2020/cm01/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087308/GridSquare_20181204_115820.jpg", pyarchFilePath)

    def test_findDefectFilePath(self):
        topDirectory = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        tifDir, firstTifFileName, defectFilePath, dm4FilePath = UtilsPath.findSerialEMFilePaths(topDirectory)
        print(tifDir)
        print(firstTifFileName)
        print(defectFilePath)
        print(dm4FilePath)
        self.assertTrue(os.path.exists(os.path.join(tifDir, firstTifFileName)))
        self.assertTrue(os.path.exists(defectFilePath))
        self.assertTrue(os.path.exists(dm4FilePath))

    def test_serialEMFilesPattern(self):
        topDirectory = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        tifDir = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data"
        filesPattern = UtilsPath.serialEMFilesPattern(topDirectory, tifDir)
        print(filesPattern)
        self.assertEqual('*/*.tif', filesPattern)
        topDirectory = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        tifDir = "/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/grid5/data/140"
        filesPattern = UtilsPath.serialEMFilesPattern(topDirectory, tifDir)
        print(filesPattern)
        self.assertEqual('*/*/*/*.tif', filesPattern)


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
