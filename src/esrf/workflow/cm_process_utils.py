import glob
import os

import motioncorr.constants

from esrf.utils.esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_ispyb import UtilsISPyB


def get_firstMovieFullPath(config_dict: dict) -> str:
    listMovies = glob.glob(
        os.path.join(config_dict["dataDirectory"], config_dict["filesPattern"])
    )
    noMovies = len(listMovies)

    if config_dict["secondGrid"] or config_dict["thirdGrid"]:
        if config_dict["secondGrid"] and config_dict["thirdGrid"]:
            raise RuntimeError(
                "`secondGrid` and `thirdGrid` cannot be used at the same time!"
            )
        if noMovies > 0:
            raise RuntimeError(
                "`secondGrid` or `thirdGrid` used and images already exists on disk!"
            )
        # Check that we have voltage, imagesCount and magnification:
        for key in ["voltage", "magnification", "imagesCount"]:
            if key not in config_dict or config_dict[key] is None:
                raise RuntimeError(
                    f"`secondGrid` or `thirdGrid` used, missing argument `{key}`!"
                )
        # Assume EPU TIFF data
        config_dict["dataType"] = 1  # "EPU_TIFF"
        config_dict["gainFlip"] = motioncorr.constants.FLIP_LEFTRIGHT
        config_dict["gainRot"] = motioncorr.constants.ROTATE_180
        config_dict[
            "filesPattern"
        ] = "Images-Disc*/GridSquare_*/Data/FoilHole_*_fractions.tiff"

    elif noMovies == 0:
        raise RuntimeError(
            f"ERROR! No movies available in directory `{config_dict['dataDirectory']}` with the filesPattern `{config_dict['filesPattern']}`"
        )
    else:
        print(f"Number of movies available on disk: {noMovies}")
        firstMovieFullPath = listMovies[0]
        print(f"First movie full path file: `{firstMovieFullPath}`")

    if noMovies == 0:
        if config_dict["secondGrid"] or config_dict["thirdGrid"]:
            print("Will wait for images from second or third grid.")
            firstMovieFullPath = None
        else:
            raise RuntimeError(
                f"ERROR - no files in direcory `{config_dict['dataDirectory']}` found with the pattern `{config_dict['filesPattern']}`"
            )
    else:
        firstMovieFullPath = listMovies[0]

    return firstMovieFullPath


def update_config_from_xml(config_dict: dict, firstMovieFullPath: str) -> None:
    if not config_dict["secondGrid"] and not config_dict["thirdGrid"]:
        if firstMovieFullPath.endswith("tiff"):
            print("********** EPU tiff data **********")
            config_dict["dataType"] = 1  # "EPU_TIFF"
            config_dict["gainFlip"] = motioncorr.constants.FLIP_LEFTRIGHT
            config_dict["gainRot"] = motioncorr.constants.ROTATE_180

            jpeg, mrc, xml, gridSquareThumbNail = UtilsPath.getEpuTiffMovieJpegMrcXml(
                firstMovieFullPath
            )
            if xml is None:
                raise RuntimeError(
                    f"Error! Cannot find metadata files in the directory which contains the following movie: {firstMovieFullPath}"
                )
            dictResults = UtilsPath.getXmlMetaData(xml)
            config_dict["doPhaseShiftEstimation"] = dictResults["phasePlateUsed"]
            config_dict["magnification"] = int(dictResults["magnification"])
            config_dict["voltage"] = int(dictResults["accelerationVoltage"])
            config_dict["imagesCount"] = int(dictResults["numberOffractions"])
        elif firstMovieFullPath.endswith("eer"):
            print("********** EER data **********")
            config_dict["dataType"] = 3  # "EER"


def get_proposal(config_dict: dict) -> str:
    proposal = UtilsISPyB.getProposal(config_dict["dataDirectory"])
    config_dict["proposal"] = proposal
    return proposal


def get_ispyb_db(config_dict: dict) -> int:
    if config_dict["noISPyB"]:
        print("No upload to ISPyB or iCAT")
        config_dict["db"] = -1
        return config_dict["db"]

    proposal = get_proposal(config_dict)

    if proposal is None:
        print("WARNING! No data will be uploaded to ISPyB.")
        db = 3
    else:
        if proposal == "mx415":
            # Use valid data base
            print("ISPyB valid data base used")
            db = 1
        elif proposal == "mx2112":
            # Use valid data base
            print("ISPyB production data base used")
            db = 0
        else:
            # Use productiond data base
            print("ISPyB production data base used")
            db = 0

    config_dict["db"] = db
    return config_dict["db"]
