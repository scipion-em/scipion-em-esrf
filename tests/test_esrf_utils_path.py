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
import glob
import pprint
import pathlib
import shutil
import tempfile
import unittest

from esrf.utils.esrf_utils_path import UtilsPath


class Test(unittest.TestCase):
    def test_getMovieFileNameParametersFromMotioncorrPath(self):
        # Test 1
        mrcFullPath1 = "/mntdirect/_data_visitor/mx2006/cm01/20180123/PROCESSED_DATA/sa1mgml/saribs/Runs/000058_ProtMotionCorr/extra/GridSquare_22879601_Data_FoilHole_22888571_Data_22885672_22885673_20180124_0845-4482_aligned_mic.mrc"
        dictResult1 = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(
            mrcFullPath1
        )
        refDict1 = {
            "data": "_Data_",
            "date": "20180124",
            "directory": "/mntdirect/_data_visitor/mx2006/cm01/20180123/PROCESSED_DATA/sa1mgml/saribs/Runs/000058_ProtMotionCorr/extra",
            "extra": "_aligned_mic",
            "gridSquare": "GridSquare_22879601",
            "hour": "0845",
            "id1": "22888571",
            "id2": "22885672",
            "id3": "22885673",
            "movieName": "FoilHole_22888571_Data_22885672_22885673_20180124_0845-4482",
            "movieNumber": "4482",
            "prefix": "FoilHole",
            "suffix": "mrc",
        }
        self.assertEqual(refDict1, dictResult1)

    def test_getMovieFileNameParametersFromMotioncorrPath_2(self):
        # Test 2
        mrcFullPath2 = "/users/svensson/ScipionUserData/projects/TestPipeLine/Runs/000859_ProtMotionCorr/extra/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344_aligned_mic.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParametersFromMotioncorrPath(
            mrcFullPath2
        )
        refDict2 = {
            "data": None,
            "date": "20170619",
            "directory": "/users/svensson/ScipionUserData/projects/TestPipeLine/Runs/000859_ProtMotionCorr/extra",
            "extra": "_aligned_mic",
            "gridSquare": None,
            "hour": "2101",
            "id1": "19150795",
            "id2": "19148847",
            "id3": "19148848",
            "movieName": "FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344",
            "movieNumber": "0344",
            "prefix": "FoilHole",
            "suffix": "mrc",
        }
        self.assertEqual(refDict2, dictResult2)

    def test_getEpuTiffMovieFileNameParametersFromMotioncorrPath(self):
        # Test 1
        # mrcFullPath1 = "/data/visitor/mx2112/cm01/20210614/PROCESSED_DATA/ApoF-test1/ApoF-test1_20210616-085412/Runs/000064_ProtMotionCorr/extra/GridSquare_10847341_Data_FoilHole_10851620_Data_10853313_10853315_20210611_161457_fractions_aligned_mic.mrc"
        mrcFullPath1 = "/gpfs/easy/data/visitor/mx2369/cm01/20220620/PROCESSED_DATA/mx2369_PkV-R_Grid6_EPU/mx2369-PkV-R/Runs/000065_ProtMotionCorr/extra/Images-Disc1_GridSquare_20341956_Data_FoilHole_20233951_Data_20345306_20345308_20220620_164313_fractions_aligned_mic.mrc"
        dictResult1 = UtilsPath.getEpuTiffMovieFileNameParametersFromMotioncorrPath(
            mrcFullPath1
        )
        pprint.pprint(dictResult1)

    def test_getSerialEMMovieFileNameParametersFromMotioncorrPath(self):
        # Test 1
        mrcFullPath1 = "/mntdirect/_data_visitor/mx415/cm01/20191029/PROCESSED_DATA/mx2214/mx2214_20191029-110718/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic.mrc"
        dictResult1 = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(
            mrcFullPath1
        )
        refDict1 = {
            "directory": "/mntdirect/_data_visitor/mx415/cm01/20191029/PROCESSED_DATA/mx2214/mx2214_20191029-110718/Runs/000064_ProtMotionCorr/extra",
            "movieName": "data_mx2214_00005",
            "movieNumber": "00005",
            "prefix": "data_mx2214",
            "suffix": "mrc",
            "extra": "aligned_mic",
        }
        self.assertEqual(refDict1, dictResult1)
        # Test 2
        mrcFullPath2 = "/data/visitor/mx2112/cm01/20191029/PROCESSED_DATA/mx2214_1/mx2214_1_20191029-134731/Runs/000064_ProtMotionCorr/extra/grid5_data_140_mx2214_140_00001_aligned_mic.mrc"
        dictResult2 = UtilsPath.getSerialEMMovieFileNameParametersFromMotioncorrPath(
            mrcFullPath2
        )
        refDict2 = {
            "directory": "/data/visitor/mx2112/cm01/20191029/PROCESSED_DATA/mx2214_1/mx2214_1_20191029-134731/Runs/000064_ProtMotionCorr/extra",
            "movieName": "grid5_data_140_mx2214_140_00001",
            "movieNumber": "00001",
            "prefix": "grid5_data_140_mx2214_140",
            "suffix": "mrc",
            "extra": "aligned_mic",
        }
        self.assertEqual(refDict2, dictResult2)

    def test_getMovieFileNameParameters(self):
        # Test1
        movieFullPath1 = "/users/svensson/cryoem/CWAT_ESRF_RawData_K2/170619_bGal1/Images-Disc1/GridSquare_19141127/Data/FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344.mrc"
        dictResult1 = UtilsPath.getMovieFileNameParameters(movieFullPath1)
        refDict1 = {
            "date": "20170619",
            "directory": "/users/svensson/cryoem/CWAT_ESRF_RawData_K2/170619_bGal1/Images-Disc1/GridSquare_19141127/Data",
            "extra": "",
            "gridSquare": "GridSquare_19141127",
            "hour": "2101",
            "id1": "19150795",
            "id2": "19148847",
            "id3": "19148848",
            "movieName": "FoilHole_19150795_Data_19148847_19148848_20170619_2101-0344",
            "movieNumber": "0344",
            "prefix": "FoilHole",
            "suffix": "mrc",
        }
        self.assertEqual(refDict1, dictResult1)
        # Test 2
        mrcFullPath2 = "/data/visitor/mx415/cm01/20180315/RAW_DATA/EPU_BSA_grid5_2mg_2_test8/Images-Disc1/GridSquare_15806527/Data/FoilHole_15814308_Data_15808956_15808957_20180317_1109-17665.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParameters(mrcFullPath2)
        refDict2 = {
            "date": "20180317",
            "directory": "/data/visitor/mx415/cm01/20180315/RAW_DATA/EPU_BSA_grid5_2mg_2_test8/Images-Disc1/GridSquare_15806527/Data",
            "extra": "",
            "gridSquare": "GridSquare_15806527",
            "hour": "1109",
            "id1": "15814308",
            "id2": "15808956",
            "id3": "15808957",
            "movieName": "FoilHole_15814308_Data_15808956_15808957_20180317_1109-17665",
            "movieNumber": "17665",
            "prefix": "FoilHole",
            "suffix": "mrc",
        }
        self.assertEqual(refDict2, dictResult2)
        # Test 3 - CRYOEM-33
        mrcFullPath2 = "/data/cm01/cmihr3/IH-LS3226/20191004/RAW_DATA/epu-grid4/Images-Disc1/GridSquare_3931883/Data/FoilHole_3936249_Data_3945596_3945597_20191004_1443-gain-ref.mrc"
        dictResult2 = UtilsPath.getMovieFileNameParameters(mrcFullPath2)
        refDict2 = None
        self.assertEqual(refDict2, dictResult2)

    def test_getEpuTiffMovieFileNameParameters(self):
        # Test - EPU Tiff
        tiffFullPath = "/data/cm01/commissioning/K3_commissioning/ApoF-test1/Images-Disc1/GridSquare_10847244/Data/FoilHole_10859740_Data_10853322_10853324_20210611_233928_fractions.tiff"
        dictResult3 = UtilsPath.getEpuTiffMovieFileNameParameters(tiffFullPath)
        refDict3 = {
            "date": "20210611",
            "directory": "/data/cm01/commissioning/K3_commissioning/ApoF-test1/Images-Disc1/GridSquare_10847244/Data",
            "gridSquare": "GridSquare_10847244",
            "hour": "233928",
            "id1": "10859740",
            "id2": "10853322",
            "id3": "10853324",
            "movieName": "FoilHole_10859740_Data_10853322_10853324_20210611_233928_fractions",
            "movieNumber": "11233928",
            "prefix": "FoilHole",
            "suffix": "tiff",
        }
        self.assertEqual(refDict3, dictResult3)
        # Test - EPU Tiff
        tiffFullPath = "/data/visitor/mx2263/cm01/20210628/RAW_DATA/mx2263_vDLPA_grid1_EPU/Images-Disc1/GridSquare_28833986/Data/FoilHole_29901259_Data_28850949_28850951_20210630_051336_fractions.tiff"
        dictResult4 = UtilsPath.getEpuTiffMovieJpegMrcXml(tiffFullPath)
        pprint.pprint(dictResult4)

    def test_getSerialEMMovieFileNameParameters(self):
        # Test1
        topDir1 = (
            "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        )
        movieFullPath1 = "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data/mx2214_00005.tif"
        dictResult1 = UtilsPath.getSerialEMMovieFileNameParameters(
            topDir1, movieFullPath1
        )
        refDict1 = {
            "directory": "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data",
            "movieName": "data_mx2214_00005",
            "movieNumber": "00005",
            "prefix": "data_mx2214",
            "suffix": "tif",
        }
        self.assertEqual(refDict1, dictResult1)
        # Test2
        topDir2 = "/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214"
        movieFullPath2 = "/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214/grid5/data/140/mx2214_140_00001.tif"
        dictResult2 = UtilsPath.getSerialEMMovieFileNameParameters(
            topDir2, movieFullPath2
        )
        refDict2 = {
            "directory": "/data/visitor/mx2112/cm01/20191029/RAW_DATA/mx2214/grid5/data/140",
            "movieName": "grid5_data_140_mx2214_140_00001",
            "movieNumber": "00001",
            "prefix": "grid5_data_140_mx2214_140",
            "suffix": "tif",
        }
        self.assertEqual(refDict2, dictResult2)

    def test_getMovieJpegMrcXml(self):
        movieFullPath = "/data/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448-3385.mrc"
        jpeg, mrc, xml, gridSquareThumbNail = UtilsPath.getMovieJpegMrcXml(
            movieFullPath
        )
        jpegRef = "/data/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.jpg"
        self.assertEqual(jpegRef, jpeg)
        mrcRef = "/data/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.mrc"
        self.assertEqual(mrcRef, mrc)
        xmlRef = "/data/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/Data/FoilHole_23724105_Data_23724797_23724798_20171123_1448.xml"
        self.assertEqual(xmlRef, xml)
        gridSquareThumbNailRef = "/data/scisoft/pxsoft/data/cryoem/20171123/RAW_DATA/testsecretin-grid1/Images-Disc1/GridSquare_23722826/GridSquare_20171123_144119.jpg"
        self.assertEqual(gridSquareThumbNailRef, gridSquareThumbNail)

    def test_getAlignMoviesPngLogFilePath(self):
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic.mrc"
        dictResult = UtilsPath.getAlignMoviesPngLogFilePath(mrcFilePath)
        dictRef = {
            "doseWeightMrc": "/data/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_aligned_mic_DW.mrc",
            "globalShiftPng": "/data/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_global_shifts.png",
            "logFileFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/logs/run.stdout",
            "thumbnailPng": "/data/scisoft/pxsoft/data/cryoem/testRunData/20171113/Runs/000056_ProtMotionCorr/extra/FoilHole_9208892_Data_9209286_9209287_20171109_1540-0539_thumbnail.png",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getEpuTiffAlignMoviesPngLogFilePath(self):
        mrcFilePath = "/data/visitor/mx2112/cm01/20220630/PROCESSED_DATA/ih-ls3403_MTb-56_Blue3/mx2112_test1_g1_20220630-155702/Runs/000065_ProtMotionCorr/extra/Images-Disc1_GridSquare_29820840_Data_FoilHole_30945883_Data_29822705_29822707_20220630_091041_fractions_aligned_mic.mrc"
        dictResult = UtilsPath.getEpuTiffAlignMoviesPngLogFilePath(mrcFilePath)
        pprint.pprint(dictResult)

    def test_getSerialEMAlignMoviesPngLogFilePath(self):
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic.mrc"
        dictResult = UtilsPath.getSerialEMAlignMoviesPngLogFilePath(mrcFilePath)
        dictRef = {
            "doseWeightMrc": "/data/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_aligned_mic_DW.mrc",
            "globalShiftPng": "/data/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_global_shifts.png",
            "logFileFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/logs/run.stdout",
            "thumbnailPng": "/data/scisoft/pxsoft/data/cryoem/testRunData/20191028/Runs/000064_ProtMotionCorr/extra/data_mx2214_00005_thumbnail.png",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getShiftData(self):
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20230513/Runs/000066_ProtMotionCorr/extra/Images-Disc1_GridSquare_12458340_Data_FoilHole_14698958_Data_14692990_14692992_20230514_115604_fractions_aligned_mic.mrc"
        dictResult = UtilsPath.getShiftData(mrcFilePath)
        dictRef = {"averageMotionPerFrame": 1.7, "noPoints": 40, "totalMotion": 66.0}
        self.assertEqual(dictRef, dictResult)

    def test_getShiftData_ts(self):
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20230502/Runs/000066_ProtMotionCorr/extra/grid1_Position_17_041_67.00_20230302_041728_fractions_aligned_mic.mrc"
        dictResult = UtilsPath.getShiftData(mrcFilePath)
        pprint.pprint(dictResult)
        dictRef = {"averageMotionPerFrame": 158.2, "noPoints": 5, "totalMotion": 791.2}
        self.assertEqual(dictRef, dictResult)

    def test_getXmlMetaData(self):
        xmlMetaDataFullPath = "/data/scisoft/pxsoft/data/cryoem/testMetaData/supervisor_20171115_150623/Images-Disc1/GridSquare_15441375/Data/FoilHole_15445484_Data_15444206_15444207_20171115_1620.xml"
        dictResult = UtilsPath.getXmlMetaData(xmlMetaDataFullPath)
        dictRef = {
            "accelerationVoltage": "300000",
            "acquisitionDateTime": "2017-11-15T16:20:52.2530023+01:00",
            "dose": "2.3276455783574426E+21",
            "magnification": "130000",
            "numberOffractions": "30",
            "phasePlateUsed": "true",
            "positionX": "0.00026971729600000011",
            "positionY": "0.00014176793600000005",
            "superResolutionFactor": "1",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getMdocMetaData(self):
        mdocMetaDataFullPath = "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data/mx2214_00005.tif.mdoc"
        dictResult = UtilsPath.getMdocMetaData(mdocMetaDataFullPath)
        import pprint

        pprint.pprint(dictResult)
        dictRef = {
            "Binning": "1",
            "CameraIndex": "1",
            "CountsPerElectron": "1",
            "DateTime": "05-Sep-19  15:52:08",
            "DefectFile": "defects_bgal-215k-img-shift_0001.txt",
            "Defocus": "0.0853802",
            "DividedBy2": "0",
            "ExposureDose": "0",
            "ExposureTime": "6",
            "FilterSlitAndLoss": "20 0",
            "FrameDosesAndNumber": "0 40",
            "GainReference": "CountRef_mx2214_00005.dm4",
            "ImageShift": "-0.643144 -0.233229",
            "Intensity": "0.116205",
            "MagIndex": "32",
            "Magnification": "130000",
            "MultishotHoleAndPosition": "1 1",
            "NavigatorLabel": "78-1",
            "NumSubFrames": "40",
            "OperatingMode": "1",
            "PixelSpacing": "1.082",
            "RotationAngle": "174.52",
            "SpotSize": "6",
            "StagePosition": "-62.6189 730.271",
            "StageZ": "-32.565",
            "SubFramePath": "X:\\DoseFractions\\mx2214\\data\\mx2214_00005.tif",
            "T": "SerialEM: Acquired on Titan Krios D3693                 05-Sep-19  11:24:48",
            "TargetDefocus": "-2.6",
            "TiltAngle": "0.00577417",
            "Voltage": "300",
            "[FrameSet": "0]",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getCtfMetaData(self):
        workingDir = (
            "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf"
        )
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000064_ProtMotionCorr/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic.mrc"
        dictResult = UtilsPath.getCtfMetaData(workingDir, mrcFilePath)
        dictRef = {
            "Angle": "35.60",
            "CCC": "-0.076290",
            "Defocus_U": "23173.92",
            "Defocus_V": "22988.54",
            "Phase_shift": None,
            "estimatedBfactor": "82.54",
            "logFilePath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/logs/run.stdout",
            "resolutionLimit": "3.381",
            "spectraImageFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.mrc",
            "spectraImageSnapshotFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.jpeg",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getCtfMetaData_2(self):
        workingDir = (
            "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf"
        )
        mrcFilePath = "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000064_ProtMotionCorr/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic.mrc"
        dictResult = UtilsPath.getCtfMetaData(workingDir, mrcFilePath)
        dictRef = {
            "Angle": "35.60",
            "CCC": "-0.076290",
            "Defocus_U": "23173.92",
            "Defocus_V": "22988.54",
            "Phase_shift": None,
            "estimatedBfactor": "82.54",
            "logFilePath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/logs/run.stdout",
            "resolutionLimit": "3.381",
            "spectraImageFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.mrc",
            "spectraImageSnapshotFullPath": "/data/scisoft/pxsoft/data/cryoem/testRunData/20190715/000126_ProtGctf/extra/GridSquare_7828225_Data_FoilHole_8853794_Data_7832898_7832899_20190711_0913-4443_aligned_mic_ctf.jpeg",
        }
        self.assertEqual(dictRef, dictResult)

    def test_getTSCtfMetaData(self):
        working_dir = pathlib.Path(
            "/data/visitor/mx2112/cm01/20230502/PROCESSED_DATA/grid1/mx2112_test_grid1_20230502-112619/Runs/000132_ProtGctf"
        )
        movie_name = "grid1_Position_13_001_17.00_20230302_005937_fractions"
        dict_result = UtilsPath.getTSCtfMetaData(working_dir, movie_name)
        pprint.pprint(dict_result)
        dict_ref = {
            "Angle": "48.83",
            "CCC": "0.001816",
            "Defocus_U": "13964.01",
            "Defocus_V": "16052.90",
            "Phase_shift": None,
            "estimatedBfactor": "0.00",
            "logFilePath": "/data/visitor/mx2112/cm01/20230502/PROCESSED_DATA/grid1/mx2112_test_grid1_20230502-112619/Runs/000132_ProtGctf/logs/run.stdout",
            "resolutionLimit": "16.413",
        }
        self.assertEqual(dict_ref, dict_result)

    def test_getPyarchFilePath(self):
        mrcFilePath = "/data/visitor/mx415/cm01/20171108/RAW_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198.mrc"
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2017/cm01/mx415/20171108/RAW_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198.mrc",
            pyarch_file_path,
        )
        mrcFilePath = "/mntdirect/_data_visitor/mx415/cm01/20171108/PROCESSED_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc"
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2017/cm01/mx415/20171108/PROCESSED_DATA/test2/CWAT_ESRF_RawData_K2/170620_TMV_1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc",
            pyarch_file_path,
        )
        # ihls2975...
        mrcFilePath = "/mntdirect/_data_cm01_inhouse/Hons/IH-LS-2975/RAW_DATA/grid1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc"
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2018/cm01/ihls2975/Hons/RAW_DATA/grid1/Images-Disc1/GridSquare_20174003/Data/GridSquare_20174003_test2/Runs/000056_ProtMotionCorr/extra/FoilHole_20182354_Data_20179605_20179606_20170620_1523-1198_aligned_mic.mrc",
            pyarch_file_path,
        )
        mrcFilePath = (
            "/mntdirect/_data_cm01_inhouse/opcm01/20171108/RAW_DATA/nicetest/Frame.mrc"
        )
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2023/20171108/opcm01/RAW_DATA/nicetest/Frame.mrc",
            pyarch_file_path,
        )
        # CRYOEM-25 : New paths for inhouse research...
        mrcFilePath = "/data/cm01/cmihr2/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087556/Data/FoilHole_4118111_Data_5127341_5127342_20181205_1023.jpg"
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2018/cm01/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087556/Data/FoilHole_4118111_Data_5127341_5127342_20181205_1023.jpg",
            pyarch_file_path,
        )
        mrcFilePath = "/mntdirect/_data_cm01_cmihr2/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087308/GridSquare_20181204_115820.jpg"
        pyarch_file_path = UtilsPath.getPyarchFilePath(mrcFilePath)
        self.assertEqual(
            "/data/pyarch/2023/cm01/IH-LS3198/20181203/RAW_DATA/EPU_IH_LS3198/Images-Disc1/GridSquare_3087308/GridSquare_20181204_115820.jpg",
            pyarch_file_path,
        )
        file_path = "/mnt/multipath-shares/data/visitor/mx2112/cm01/20221017/PROCESSED_DATA/mx2440_RESC_Grid_4_EPU/mx2112_RESC_grid4_20221017-140309/Runs/000066_ProtMotionCorr/extra/Images-Disc1_GridSquare_10177155_Data_FoilHole_10275476_Data_10274776_10274778_20221010_180120_fractions_thumbnail.png"
        pyarch_file_path = UtilsPath.getPyarchFilePath(file_path)
        self.assertEqual(
            "/data/pyarch/2023/cm01/mx2112/20221017/PROCESSED_DATA/mx2440_RESC_Grid_4_EPU/mx2112_RESC_grid4_20221017-140309/Runs/000066_ProtMotionCorr/extra/Images-Disc1_GridSquare_10177155_Data_FoilHole_10275476_Data_10274776_10274778_20221010_180120_fractions_thumbnail.png",
            pyarch_file_path,
        )

    # def test_getPyarchFilePath_1(self):
    #     # /mnt/multipath-shares/tmp_14_days
    #     logFilePath = "/mnt/multipath-shares/scisoft/cm01/visitor/mx2260/20210402/PROCESSED_DATA/mx2260_grid1_CBC_EPU/mx2260_CBC/Runs/000124_ProtGctf/logs/run.stdout"
    #     pyarchFilePath = UtilsPath.getPyarchFilePath(logFilePath)
    #     self.assertEqual(
    #         "/data/pyarch/2021/cm01/mx2260/20210402/PROCESSED_DATA/mx2260_grid1_CBC_EPU/mx2260_CBC/Runs/000124_ProtGctf/logs/run.stdout",
    #         pyarchFilePath,
    #     )
    #     # logFilePath = "/data/visitor/mx2346/cm01/20210329/RAW_DATA/mx2346_Grid4_R217H_EPU/Images-Disc1/GridSquare_29246918/GridSquare_20210329_132858.jpg"
    #     # pyarchFilePath = UtilsPath.getPyarchFilePath(logFilePath)
    #     # self.assertEqual("/data/pyarch/2021/cm01/mx2346/20210329/PROCESSED_DATA/mx2346_R217H_11/Runs/000124_ProtGctf/logs/run.stdout", pyarchFilePath)

    def test_findDefectFilePath(self):
        topDirectory = (
            "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        )
        (
            tifDir,
            firstTifFileName,
            defectFilePath,
            dm4FilePath,
        ) = UtilsPath.findSerialEMFilePaths(topDirectory)
        print(tifDir)
        print(firstTifFileName)
        print(defectFilePath)
        print(dm4FilePath)
        self.assertTrue(os.path.exists(os.path.join(tifDir, firstTifFileName)))
        self.assertTrue(os.path.exists(defectFilePath))
        self.assertTrue(os.path.exists(dm4FilePath))

    def test_serialEMFilesPattern(self):
        topDirectory = (
            "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        )
        tifDir = "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/data"
        filesPattern = UtilsPath.serialEMFilesPattern(topDirectory, tifDir)
        print(filesPattern)
        self.assertEqual("*/*.tif", filesPattern)
        topDirectory = (
            "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214"
        )
        tifDir = "/data/scisoft/pxsoft/data/cryoem/testSerialEmData/20190905/RAW_DATA/mx2214/grid5/data/140"
        filesPattern = UtilsPath.serialEMFilesPattern(topDirectory, tifDir)
        print(filesPattern)
        self.assertEqual("*/*/*/*.tif", filesPattern)

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

    def test_getBlackFileList(self):
        dataDirectory = (
            "/data/visitor/mx2260/cm01/20210122/RAW_DATA/mx2260_grid5_EXTs_EPU"
        )
        filesPattern = "Images-Disc*/GridSquare_*/Data/FoilHole_*-*.mrc"
        listMovies = glob.glob(os.path.join(dataDirectory, filesPattern))
        allParamsJsonFile = "/data/visitor/mx2260/cm01/20210122/PROCESSED_DATA/mx2260_grid5_EXTs_EPU/allParams.json"
        blackList = UtilsPath.getBlacklist(listMovies, allParamsJsonFile)
        import pprint

        pprint.pprint(blackList)

    def test_getBlackFileList_2(self):
        dataDirectory = (
            "/data/visitor/mx2261/cm01/20210702/RAW_DATA/mx2261_IgIF_grid4_EPU"
        )
        filesPattern = "Images-Disc*/GridSquare_*/Data/FoilHole_*_fractions.tiff"
        listMovies = glob.glob(os.path.join(dataDirectory, filesPattern))
        allParamsJsonFile = "/data/visitor/mx2261/cm01/20210702/PROCESSED_DATA/mx2261_IgIF_grid4_EPU/allParams.json"
        blackList = UtilsPath.getBlacklistAllMovies(listMovies, allParamsJsonFile)
        print(len(blackList))
        # import pprint
        # pprint.pprint(blackList)

    def test_getInputParticleDict(self):
        testDataPath = pathlib.Path(__file__).parent / "testdata"
        allParamsFile = str(testDataPath / "allParams.json")
        allParams = json.loads(open(allParamsFile).read())
        # pprint.pprint(allParams)
        inputParticlesStarFile = str(testDataPath / "input_particles.star")
        dictInputParticles = UtilsPath.getInputParticleDict(
            pathToInputParticlesStarFile=inputParticlesStarFile, allParams=allParams
        )
        pprint.pprint(dictInputParticles)

    def test_parseRelionModelStarFile(self):
        testDataPath = pathlib.Path(__file__).parent / "testdata"
        starFile = str(testDataPath / "relion_it025_model.star")
        dictStarFile = UtilsPath.parseRelionModelStarFile(starFile)
        pprint.pprint(dictStarFile)

    def test_getTomoMovieFileNameParameters_rawMovie(self):
        file_path = "/data/scisoft/pxsoft/data/cryoem/ihls3478/cm01/20230301/RAW_DATA/grid1/grid1_Position_1_030_54.50_20230301_174921_fractions.tiff"
        dict_movie = UtilsPath.getTSFileParameters(file_path)
        pprint.pprint(dict_movie)
        self.assertEqual(
            dict_movie["directory"],
            "/data/scisoft/pxsoft/data/cryoem/ihls3478/cm01/20230301/RAW_DATA/grid1",
        )
        self.assertEqual(dict_movie["grid_name"], "grid1")
        self.assertEqual(dict_movie["ts_name"], "grid1_Position_1")
        self.assertEqual(dict_movie["movie_number"], 30)
        self.assertEqual(dict_movie["tilt_angle"], 54.50)
        self.assertEqual(dict_movie["date"], "20230301")
        self.assertEqual(dict_movie["time"], "174921")

    def test_getTomoMovieFileNameParameters_rawMovie_2(self):
        file_path = "/data/visitor/ihls3501/cm01/20230523/RAW_DATA/grid5-test-tomo-processing/test_1_001_0.00_20230525_155045_fractions.tiff"
        dict_movie = UtilsPath.getTSFileParameters(file_path)
        pprint.pprint(dict_movie)
        self.assertEqual(
            dict_movie["directory"],
            "/data/visitor/ihls3501/cm01/20230523/RAW_DATA/grid5-test-tomo-processing",
        )
        self.assertEqual(dict_movie["grid_name"], "grid5-test-tomo-processing")
        self.assertEqual(dict_movie["ts_name"], "test_1")
        self.assertEqual(dict_movie["movie_number"], 1)
        self.assertEqual(dict_movie["tilt_angle"], 0.00)
        self.assertEqual(dict_movie["date"], "20230525")
        self.assertEqual(dict_movie["time"], "155045")

    def test_getTomoMovieFileNameParameters_motionCor(self):
        file_path = "/mnt/multipath-shares/data/visitor/mx2112/cm01/20230421/PROCESSED_DATA/grid1/mx2112_test_grid1_20230421-172001/Runs/000066_ProtMotionCorr/extra/grid1_Position_1_001_17.00_20230301_172443_fractions_aligned_mic.mrc"
        dict_movie = UtilsPath.getTSFileParameters(file_path)
        pprint.pprint(dict_movie)
        self.assertEqual(
            dict_movie["directory"],
            "/mnt/multipath-shares/data/visitor/mx2112/cm01/20230421/PROCESSED_DATA/grid1/mx2112_test_grid1_20230421-172001/Runs/000066_ProtMotionCorr/extra",
        )
        self.assertEqual(dict_movie["grid_name"], "grid1")
        self.assertEqual(dict_movie["ts_name"], "grid1_Position_1")
        self.assertEqual(dict_movie["movie_number"], 1)
        self.assertEqual(dict_movie["tilt_angle"], 17.00)
        self.assertEqual(dict_movie["date"], "20230301")
        self.assertEqual(dict_movie["time"], "172443")

    def test_createIcatDirectory(self):
        test_dir = pathlib.Path(tempfile.mkdtemp())
        movie_directory = test_dir / "grid1"
        movie_directory.mkdir(mode=0o755)
        movie_full_path = (
            movie_directory
            / "grid1_Position_8_001_17.00_20230301_220611_fractions.tiff"
        )
        icat_movie_path = UtilsPath.createIcatDirectory(str(movie_full_path))

    def test_createTiltSerieInstrumentSnapshot(self):
        test_dir = pathlib.Path(tempfile.mkdtemp())
        movie_directory = test_dir / "grid1"
        movie_directory.mkdir(mode=0o755)
        movie_full_path = (
            movie_directory
            / "grid1_Position_8_001_17.00_20230301_220611_fractions.tiff"
        )
        # Copy "real" movie
        real_movie_path = "/data/scisoft/pxsoft/data/cryoem/ihls3478/cm01/20230301/RAW_DATA/grid1/grid1_Position_1_030_54.50_20230301_174921_fractions.tiff"
        shutil.copy(real_movie_path, movie_full_path)
        icat_movie_path = UtilsPath.createIcatDirectory(str(movie_full_path))
        print(icat_movie_path)
        UtilsPath.createTiltSerieInstrumentSnapshot(icat_movie_path)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
