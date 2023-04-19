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
import sys
import json
import time
import pprint
import unittest
import pathlib


from esrf.utils.esrf_utils_icat import UtilsIcat


class Test(unittest.TestCase):
    def tes_uploadToIcat(self):
        listFiles = [
            "/data/visitor/mx2005/cm01/20171209/RAW_DATA/"
            + "baseplate-epu-grid2/Images-Disc1/GridSquare_7259648/Data/"
            + "FoilHole_7265309_Data_7264706_7264707_20171207_1704-10925.mrc"
        ]
        directory = "/data/visitor/mx2005/cm01/20171209/RAW_DATA/baseplate-epu-grid2"
        proposal = "id310009"
        sample = "sample1"
        dataSetName = "GridSquare_7259648_{0}".format(round(time.time()))
        dictMetadata = {
            "EM_amplitude_contrast": 0.0,
            "EM_dose_initial": 1.0,
            "EM_dose_per_frame": 2.0,
            "EM_images_count": 3.0,
            "EM_magnification": 4.0,
            "EM_position_x": 5.0,
            "EM_position_y": 6.0,
            "EM_protein_acronym": 7.0,
            "EM_sampling_rate": 8.0,
            "EM_spherical_aberration": 9.0,
            "EM_voltage": 10.0,
        }
        UtilsIcat.uploadToIcat(
            listFiles, directory, proposal, sample, dataSetName, dictMetadata
        )

    def findStartEndTime(self, listMovies):
        startTime = None
        endTime = None
        for moviePath in listMovies:
            movieDateTime = " ".join(moviePath.split("_")[-2:])
            movieDateTime = movieDateTime.split("-")[0]
            # print(movieDateTime)
            if startTime is None or startTime > movieDateTime:
                startTime = movieDateTime
            if endTime is None or endTime < movieDateTime:
                endTime = movieDateTime
        # print(startTime, endTime)
        return startTime, endTime

    def archiveGridSquare(
        self, proposal, sampleAcronym, allParams, gridSquareToBeArchived
    ):
        # Archive remaining movies
        print("Archiving grid square: {0}".format(gridSquareToBeArchived))
        listPathsToBeArchived = []
        sumPositionX = 0.0
        sumPositionY = 0.0
        indexPosition = 0
        for movieName in allParams:
            if (
                "gridSquare" in allParams[movieName]
                and allParams[movieName]["gridSquare"] == gridSquareToBeArchived
                and not allParams[movieName]["archived"]
            ):
                listPathsToBeArchived.append(allParams[movieName]["movieFullPath"])
                allParams[movieName]["archived"] = True
                try:
                    sumPositionX += float(allParams[movieName]["positionX"])
                    sumPositionY += float(allParams[movieName]["positionY"])
                    indexPosition += 1
                except:
                    pass
        if proposal.startswith("id"):
            # Test proposal - only archive 1 movie
            listPathsToBeArchived = listPathsToBeArchived[0:1]
        noImagesToBeArchived = len(listPathsToBeArchived)
        if noImagesToBeArchived > 0:
            if indexPosition > 0:
                meanPositionX = sumPositionX / indexPosition
                meanPositionY = sumPositionY / indexPosition
            else:
                meanPositionX = None
                meanPositionY = None
            startTime, endTime = self.findStartEndTime(listPathsToBeArchived)
            dictIcatMetaData = dict(allParams["EM_meta_data"])
            dictIcatMetaData["EM_position_x"] = meanPositionX
            dictIcatMetaData["EM_position_y"] = meanPositionY
            #  '20201002 220415'
            startTime = (
                startTime[0:4]
                + "-"
                + startTime[4:6]
                + "-"
                + startTime[6:8]
                + "T"
                + startTime[9:11]
                + ":"
                + startTime[11:13]
                + ":"
                + startTime[13:15]
            )
            endTime = (
                endTime[0:4]
                + "-"
                + endTime[4:6]
                + "-"
                + endTime[6:8]
                + "T"
                + endTime[9:11]
                + ":"
                + endTime[11:13]
                + ":"
                + endTime[13:15]
            )
            dictIcatMetaData["startTime"] = startTime
            dictIcatMetaData["startDate"] = startTime
            dictIcatMetaData["endTime"] = endTime
            directory = dictIcatMetaData["EM_directory"]
            listGalleryPath = allParams[gridSquareToBeArchived]["listGalleryPath"]
            dataSetName = gridSquareToBeArchived
            allParams[dataSetName] = dictIcatMetaData
            # print("listPathsToBeArchived: {0}".format(pprint.pformat(listPathsToBeArchived)))
            print("directory: {0}".format(directory))
            print("proposal: {0}".format(proposal))
            print("sampleAcronym: {0}".format(sampleAcronym))
            print("dataSetName: {0}".format(dataSetName))
            print("dictIcatMetaData: {0}".format(pprint.pformat(dictIcatMetaData)))
            errorMessage = UtilsIcat.uploadToIcat(
                listPathsToBeArchived,
                directory,
                proposal,
                sampleAcronym,
                dataSetName,
                dictIcatMetaData,
                listGalleryPath,
            )
            if errorMessage is not None:
                print("ERROR during icat upload!")
                raise RuntimeError(errorMessage)

    def analyseEpuMovieFile(self, movie_name):
        movie_id = None
        p = re.compile(
            "(.*)_([0-9]*)_Data_([0-9]*)_([0-9]*)_([0-9]*)_([0-9]*)(.*)\.(.*)"
        )
        m = p.match(str(movie_name))
        if m is not None:
            dictResult = {}
            dictResult["prefix"] = m.group(1)
            dictResult["id1"] = m.group(2)
            dictResult["id2"] = m.group(3)
            dictResult["id3"] = m.group(4)
            dictResult["date"] = m.group(5)
            dictResult["hour"] = m.group(6)
            dictResult["movieNumber"] = m.group(7)
            movie_id = "{prefix}_{id1}_Data_{id2}_{id3}_{date}_{hour}".format(
                **dictResult
            )
        return movie_id

    def analyseEPUData(self, image_disc_path):
        dict_data = {"type": "EPU", "gridsquares": []}
        # The image dic path contains the grid squares
        for gridsquare_path in image_disc_path.iterdir():
            if str(gridsquare_path.name).startswith("GridSquare"):
                gridsquare = {"name": gridsquare_path.name, "files": [], "movies": []}
                list_movie_dict = []
                for data_entry in gridsquare_path.iterdir():
                    if data_entry.name == "Data":
                        files = list(data_entry.iterdir())
                        for file in files:
                            # Find movie mrc file
                            movie_id = self.analyseEpuMovieFile(file.name)
                            if movie_id is not None:
                                has_found_movie_id = False
                                for movie_dict in list_movie_dict:
                                    if movie_dict["movie_id"] == movie_id:
                                        movie_dict["files"].append(file)
                                        has_found_movie_id = True
                                        break
                                if not has_found_movie_id:
                                    list_movie_dict.append(
                                        {"movie_id": movie_id, "files": [file]}
                                    )
                        # Sort movies
                        list_movie_dict = sorted(
                            list_movie_dict,
                            key=lambda movie_dict: "_".join(
                                movie_dict["movie_id"].split("_")[-2:]
                            ),
                        )
                        gridsquare["movies"] = list_movie_dict
                    elif data_entry.suffix in [".jpg", ".xml"]:
                        gridsquare["files"].append(data_entry)
                if len(gridsquare["movies"]) > 0:
                    dict_data["gridsquares"].append(gridsquare)
        # Sort grid squares
        dict_data["gridsquares"] = sorted(
            dict_data["gridsquares"],
            key=lambda gridsquare: "_".join(
                gridsquare["movies"][0]["movie_id"].split("_")[-2:]
            ),
        )
        return dict_data

    def dictData2AllParams(self, dictData):
        if not dictData["type"] == "EPU":
            raise RuntimeError("Type {0} not supported!".format(dictData["type"]))
        allParams = {}
        for gridSquare in dictData["gridsquares"]:
            for path in gridSquare["files"]:
                imageName = path.name
                if imageName.endswith(".jpg"):
                    allParams[gridSquare["name"]] = {"listGalleryPath": [str(path)]}
                    break
            for movie in gridSquare["movies"]:
                movieId = movie["movie_id"]
                for path in movie["files"]:
                    fileName = path.name
                    if "-" in fileName and fileName.endswith(".mrc"):
                        movieFullPath = str(path)
                        break
                allParams[movieId] = {
                    "movieFullPath": movieFullPath,
                    "gridSquare": gridSquare["name"],
                    "archived": False,
                }
        return allParams


    def test_uploadToIcatPlus(self):
        directory = "/data/visitor/mx2112/cm01/20230405/RAW_DATA/grid1_1/grid1_Position_8/001"
        proposal = "CM012304"
        dataSetName = "001"
        dictMetadata = {
            "Sample_name": "grid1_Position_8",
            "EM_amplitude_contrast": 0.0,
            "EM_dose_initial": 1.0,
            "EM_dose_per_frame": 2.0,
            "EM_images_count": 3.0,
            "EM_magnification": 4.0,
            "EM_position_x": 5.0,
            "EM_position_y": 6.0,
            "EM_protein_acronym": 7.0,
            "EM_sampling_rate": 8.0,
            "EM_spherical_aberration": 9.0,
            "EM_voltage": 10.0,
            "EM_grid_name": "grid1",
            "EM_tilt_angle": 23.45
        }
        UtilsIcat.uploadToIcatPlus(
            directory=directory,
            proposal=proposal,
            dataSetName=dataSetName,
            dictMetadata=dictMetadata
        )

















    # def test_archive_mx2261_20201005(self):
    #     proposal = "mx2261"
    #     # proposal = "id000001"
    #     sampleAcronym = "Grid3"
    #     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2261_20201005/allParams.json"
    #     with open(allParamsFile) as fd:
    #         allParams = json.loads(fd.read())
    #     # Set all archived to false
    #     # for key in allParams:
    #     #     allParams[key]["archived"] = False
    #     # pprint.pprint(allParams)
    #     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
    #     pprint.pprint(dictGridSquares.keys())
    #     for gridSquareToBeArchived in dictGridSquares:
    #         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
    #         if not proposal.startswith("id"):
    #             with open(allParamsFile, "w") as fd:
    #                 fd.write(json.dumps(allParams, indent=4))
    #         else:
    #             sys.exit(0)
    #         # sys.exit(0)

    # def test_create_all_params_ihmx127_20200727(self):
    #     dictEmData =  {
    #         "EM_position_x": "0.0",
    #         "EM_position_y": "0.0",
    #         "EM_directory": "/data/cm01/cmihr4/IH-MX127/20200727/RAW_DATA/IH-MX127_Grid4_MsbA_EPU",
    #         "EM_voltage": 300000,
    #         "EM_dose_initial": 0.0,
    #         "EM_images_count": 40,
    #         "EM_sampling_rate": 0.827,
    #         "EM_dose_per_frame": 1.05,
    #         "EM_amplitude_contrast": 0.1,
    #         "EM_spherical_aberration": 2.7,
    #         "EM_magnification": 165000,
    #         "EM_protein_acronym": "MsbA"
    #     }
    #     dataDir = pathlib.Path(dictEmData["EM_directory"]) / "Images-Disc1"
    #     dictEpuData = self.analyseEPUData(dataDir)
    #     allParams = self.dictData2AllParams(dictEpuData)
    #     allParams["EM_meta_data"] = dictEmData
    #     with open("/home/esrf/svensson/CryoEM_archiving/ih-mx127_20200727/allParams.json", "w") as fd:
    #         fd.write(json.dumps(allParams, indent=4))

    # def test_archive_ih_mx127_20200727(self):
    #     proposal = "ih-mx127"
    #     # proposal = "id000001"
    #     sampleAcronym = "Grid4"
    #     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/ih-mx127_20200727/allParams.json"
    #     with open(allParamsFile) as fd:
    #         allParams = json.loads(fd.read())
    #     # Set all archived to false
    #     # for key in allParams:
    #     #     allParams[key]["archived"] = False
    #     # pprint.pprint(allParams)
    #     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
    #     pprint.pprint(dictGridSquares.keys())
    #     for gridSquareToBeArchived in dictGridSquares:
    #         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
    #         if not proposal.startswith("id"):
    #             with open(allParamsFile, "w") as fd:
    #                 fd.write(json.dumps(allParams, indent=4))
    #         else:
    #             sys.exit(0)
    #         # sys.exit(0)

    # def test_create_all_params_ihmx126_20200717(self):
    #     dictEmData =  {
    #         "EM_position_x": "0.0",
    #         "EM_position_y": "0.0",
    #         "EM_directory": "/data/cm01/cmihr2/IH-MX126/20200717/RAW_DATA/IH-MX126_grid12_SidH_EPU",
    #         "EM_voltage": 300000,
    #         "EM_dose_initial": 0.0,
    #         "EM_images_count": 40,
    #         "EM_sampling_rate": 0.827,
    #         "EM_dose_per_frame": 1.084,
    #         "EM_amplitude_contrast": 0.1,
    #         "EM_spherical_aberration": 2.7,
    #         "EM_magnification": 165000,
    #         "EM_protein_acronym": "SidH"
    #     }
    #     dataDir = pathlib.Path("/data/cm01/cmihr2/IH-MX126/20200717/RAW_DATA/IH-MX126_grid12_SidH_EPU/Images-Disc1")
    #     dictEpuData = self.analyseEPUData(dataDir)
    #     allParams = self.dictData2AllParams(dictEpuData)
    #     allParams["EM_meta_data"] = dictEmData
    #     with open("/home/esrf/svensson/CryoEM_archiving/ih-mx126_20200717/allParams.json", "w") as fd:
    #         fd.write(json.dumps(allParams, indent=4))
    #

    # def test_archive_ih_mx126_20200720(self):
    #     proposal = "ih-mx126"
    #     # proposal = "id000001"
    #     sampleAcronym = "g12"
    #     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/ih-mx126_20200717/allParams.json"
    #     with open(allParamsFile) as fd:
    #         allParams = json.loads(fd.read())
    #     # Set all archived to false
    #     # for key in allParams:
    #     #     allParams[key]["archived"] = False
    #     # pprint.pprint(allParams)
    #     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
    #     pprint.pprint(dictGridSquares.keys())
    #     for gridSquareToBeArchived in dictGridSquares:
    #         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
    #         if not proposal.startswith("id"):
    #             with open(allParamsFile, "w") as fd:
    #                 fd.write(json.dumps(allParams, indent=4))
    #         else:
    #             sys.exit(0)
    #         # sys.exit(0)


# def test_archive_mx2301_20200720(self):
#     proposal = "mx2301"
#     # proposal = "id000001"
#     sampleAcronym = "g10"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2301_20200720/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2300_20200715(self):
#     proposal = "mx2300"
#     # proposal = "id000001"
#     sampleAcronym = "g8"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2300_20200715/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2297_20200713(self):
#     proposal = "mx2297"
#     # proposal = "id000001"
#     sampleAcronym = "g5"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2297_20200713/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2258_20200708(self):
#     proposal = "mx2258"
#     # proposal = "id000001"
#     sampleAcronym = "Grid4b"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2258_20200708/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2303_20200706(self):
#     proposal = "mx2303"
#     # proposal = "id000001"
#     sampleAcronym = "grid2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2303_20200706/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2249_20200703(self):
#     proposal = "mx2249"
#     # proposal = "id000001"
#     sampleAcronym = "grid2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2249_20200703/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2248_20200629(self):
#     proposal = "mx2248"
#     # proposal = "id000001"
#     sampleAcronym = "Grid2-2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2248_20200629/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2250_20200622(self):
#     proposal = "mx2250"
#     # proposal = "id000001"
#     sampleAcronym = "Grid4"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2250_20200622/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_findNotArchivedMovies_mx2250_20200622(self):
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2250_20200622/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     dictArchivedGridSquare = {
#         "GridSquare_22255240": 149,
#         "GridSquare_22255234": 1064,
#         "GridSquare_22255210": 1052,
#         "GridSquare_22255208": 1036,
#         "GridSquare_22255201": 886,
#         "GridSquare_22255199": 988,
#         "GridSquare_22255197": 768,
#         "GridSquare_22255190": 181,
#         "GridSquare_22255188": 965,
#         "GridSquare_22255186": 1006,
#         "GridSquare_22255177": 887,
#     }
#     dictGridsquare = {}
#     for movie in allParams:
#         dictMovie = allParams[movie]
#         if "gridSquare" in dictMovie:
#             gridSquare = dictMovie["gridSquare"]
#             if gridSquare not in dictGridsquare:
#                 dictGridsquare[gridSquare] = []
#             dictGridsquare[gridSquare].append(movie)
#     totalNotArchived = 0
#     dictNew = {}
#     for gridSquare in dictGridsquare:
#         noMovies = len(dictGridsquare[gridSquare])
#         if gridSquare in dictArchivedGridSquare:
#             if noMovies == dictArchivedGridSquare[gridSquare]:
#                 print("{0}: all movies have been archived".format(gridSquare))
#             else:
#                 print("{0}: archived but has {1} missing movies".format(gridSquare, noMovies - dictArchivedGridSquare[gridSquare]))
#         else:
#             dictNew[gridSquare] = dictArchivedGridSquare[gridSquare]
#             print("{0}: {1} movies not archived".format(gridSquare, noMovies))
#             totalNotArchived += noMovies
#     print("totalNotArchived {0}".format(totalNotArchived))
#     # pprint.pprint(listGridSquare)


# def test_archive_mx2263_20200828(self):
#     proposal = "mx2263"
#     # proposal = "id000001"
#     sampleAcronym = "g2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2263_20200828/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2259_20200923(self):
#     proposal = "mx2259"
#     # proposal = "id000001"
#     sampleAcronym = "Grid3"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2259_20200923/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_blc12442_20201002(self):
#     proposal = "blc12442"
#     # proposal = "id000001"
#     sampleAcronym = "Grid2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/blc12442_20201002/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     # dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     listGridSquares = [
#          # 'GridSquare_1852663',
#          'GridSquare_1852661',
#          'GridSquare_1852673',
#          'GridSquare_1852659',
#          'GridSquare_1852668'
#     ]
#     pprint.pprint(listGridSquares)
#     for gridSquareToBeArchived in listGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)


# def test_findNotArchivedMovies_blc12442(self):
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/blc12442_20201002/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     dictArchivedGridSquare = {
#         "GridSquare_1852220": 444,
#         "GridSquare_1852226": 444,
#         "GridSquare_1852230": 239,
#         "GridSquare_1852232": 389,
#         "GridSquare_1852652": 237,
#         "GridSquare_1852665": 402,
#         "GridSquare_1852671": 507,
#         "GridSquare_1852677": 474,
#         "GridSquare_1852713": 464,
#         "GridSquare_1852804": 477,
#         "GridSquare_1852806": 232
#     }
#     dictGridsquare = {}
#     for movie in allParams:
#         dictMovie = allParams[movie]
#         if "gridSquare" in dictMovie:
#             gridSquare = dictMovie["gridSquare"]
#             if gridSquare not in dictGridsquare:
#                 dictGridsquare[gridSquare] = []
#             dictGridsquare[gridSquare].append(movie)
#     totalNotArchived = 0
#     dictNew = {}
#     for gridSquare in dictGridsquare:
#         noMovies = len(dictGridsquare[gridSquare])
#         if gridSquare in dictArchivedGridSquare:
#             if noMovies == dictArchivedGridSquare[gridSquare]:
#                 print("{0}: all movies have been archived".format(gridSquare))
#             else:
#                 print("{0}: archived but has {1} missing movies".format(gridSquare, noMovies - dictArchivedGridSquare[gridSquare]))
#         else:
#             dictNew[gridSquare] = dictArchivedGridSquare[gridSquare]
#             print("{0}: {1} movies not archived".format(gridSquare, noMovies))
#             totalNotArchived += noMovies
#     print("totalNotArchived {0}".format(totalNotArchived))
#     pprint.pprint(listGridSquare)
#

# import glob
# listNotArchived = []
# listFiles = glob.glob("/data/cm01/cmihr1/BLC12442/20201002/RAW_DATA/BLC12442_grid2_CodvTC_EPU/Images-Disc1/*/Data/*-*.mrc")
# for filePath in listFiles:
#     fileName = os.path.basename(filePath)
#     movieName = os.path.splitext(fileName)[0]
#     if not movieName in allParams:
#         listNotArchived.append(movieName)
#     pass
# print(len(listFiles))
# print(len(allParams))
# print(len(listNotArchived))

# def test_archive_mx2258_20200819(self):
#     proposal = "mx2258"
#     # proposal = "id000001"
#     sampleAcronym = "grid8"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2258_20200819/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         else:
#             sys.exit(0)
#         # sys.exit(0)

# def test_archive_mx2244_20200722(self):
#     proposal = "mx2244"
#     # proposal = "id000001"
#     sampleAcronym = "Grid2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2244_20200722/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         # sys.exit(0)


# def tes_archive_blc12442(self):
#     proposal = "blc12442"
#     sampleAcronym = "Grid2"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/BLC12442/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         with open(allParamsFile, "w") as fd:
#             fd.write(json.dumps(allParams, indent=4))
#         sys.exit(0)


# def test_archive_mx2261_20201104(self):
#     proposal = "mx2261"
#     # proposal = "id000001"
#     sampleAcronym = "Grid1"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2261_20201104/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         with open(allParamsFile, "w") as fd:
#             fd.write(json.dumps(allParams, indent=4))
#         sys.exit(0)

# def test_archive_mx2261_20200925(self):
#     proposal = "mx2261"
#     # proposal = "id000001"
#     sampleAcronym = "Grid3"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2261_20200925/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         with open(allParamsFile, "w") as fd:
#             fd.write(json.dumps(allParams, indent=4))
#         # sys.exit(0)

# def test_archive_mx2258_20200708(self):
#     proposal = "mx2258"
#     # proposal = "id000001"
#     sampleAcronym = "Grid4b"
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2258_20200708/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     # Set all archived to false
#     # for key in allParams:
#     #     allParams[key]["archived"] = False
#     # pprint.pprint(allParams)
#     dictGridSquares = UtilsIcat.findGridSquaresNotUploaded(allParams)
#     pprint.pprint(dictGridSquares.keys())
#     for gridSquareToBeArchived in dictGridSquares:
#         self.archiveGridSquare(proposal, sampleAcronym, allParams, gridSquareToBeArchived)
#         if not proposal.startswith("id"):
#             with open(allParamsFile, "w") as fd:
#                 fd.write(json.dumps(allParams, indent=4))
#         sys.exit(0)

# def test_findNotArchivedMovies(self):
#     allParamsFile = "/home/esrf/svensson/CryoEM_archiving/mx2261_20201104/allParams.json"
#     with open(allParamsFile) as fd:
#         allParams = json.loads(fd.read())
#     import glob
#     listFiles = glob.glob("/data/visitor/mx2261/cm01/20201104/RAW_DATA/mx2261_Grid1_TnaCwt_EPU/Images-Disc1/GridSquare*/Data/*-????.mrc")
#     for filePath in listFiles:
#         fileName = os.path.basename(filePath)
#         movieName = os.path.splitext(fileName)[0]
#         if not movieName in allParams:
#             print(movieName)
#         pass
#     print(len(listFiles))
#     print(len(allParams))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
