import os
import sys
import glob
import time
import celery

if "v3_dev" in __file__:
    sys.path.insert(0, "/opt/pxsoft/scipion/v3_dev/ubuntu20.04/scipion-em-esrf")

#
import motioncorr.constants

from esrf.utils.esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_ispyb import UtilsISPyB
from esrf.workflow.command_line_parser import getCommandlineOptions

# print(getCommandlineOptions.__module__)
config_dict = getCommandlineOptions(use_celery=True)
# config_dict = {
#     "dataDirectory": "/data/visitor/mx2112/cm01/20220426/RAW_DATA/igm-grid3-2",
#     "filesPattern": "Images-Disc1/GridSquare_*/Data/FoilHole_*_fractions.tiff",
#     "scipionProjectName": "test_celery_{0}".format(time.time()),
#     "proteinAcronym": "igm-fccore",
#     "sampleAcronym": "g3",
#     "doseInitial": 0.0,
#     "magnification": 105000,
#     "imagesCount": 40,
#     "voltage": 300000,
#     "dosePerFrame": 0.935,
#     "dataStreaming": True,
#     "alignFrame0": 1,
#     "alignFrameN": 0,
#     "phasePlateData": False,
#     "no2dClass": True,
#     "onlyISPyB": False,
#     "noISPyB": True,
#     "particleElimination": False,
#     "samplingRate": 0.84,
#     "superResolution": True,
#     "partSize": 300.0,
#     "defectMapPath": None,
#     "gainFilePath": None,
#     "secondGrid": False,
#     "proposal": "mx2112",
#     "celery_worker": "cmproc3"
# }
# Command line: --dataDirectory /data/visitor/mx2112/cm01/20220426/RAW_DATA/igm-grid3-2
# --dosePerFrame 0.935 --samplingRate 0.84
#
#
if config_dict["filesPattern"] is None:
    # No filesPattern, let's assume that we are dealing with EPU data
    config_dict[
        "filesPattern"
    ] = "Images-Disc1/GridSquare_*/Data/FoilHole_*_fractions.tiff"

# Check how many movies are present on disk
listMovies = glob.glob(
    os.path.join(config_dict["dataDirectory"], config_dict["filesPattern"])
)
noMovies = len(listMovies)
# Check how many movies are present on disk
listMovies = glob.glob(
    os.path.join(config_dict["dataDirectory"], config_dict["filesPattern"])
)
noMovies = len(listMovies)
print("********** EPU tiff data **********")
config_dict["dataType"] = 1  # "EPU_TIFF"
config_dict["gainFlip"] = motioncorr.constants.FLIP_LEFTRIGHT
config_dict["gainRot"] = motioncorr.constants.ROTATE_180
if noMovies > 0:
    # We have EPU tiff data!
    pass

firstMovieFullPath = listMovies[0]

jpeg, mrc, xml, gridSquareThumbNail = UtilsPath.getEpuTiffMovieJpegMrcXml(
    firstMovieFullPath
)

if xml is None:
    print("*" * 80)
    print("*" * 80)
    print("*" * 80)
    print(
        "Error! Cannot find metadata files in the directory which contains the following movie:"
    )
    print(firstMovieFullPath)
    print("*" * 80)
    print("*" * 80)
    print("*" * 80)
    sys.exit(1)

dictResults = UtilsPath.getXmlMetaData(xml)
config_dict["doPhaseShiftEstimation"] = dictResults["phasePlateUsed"]
config_dict["magnification"] = int(dictResults["magnification"])
config_dict["voltage"] = int(dictResults["accelerationVoltage"])
config_dict["imagesCount"] = int(dictResults["numberOffractions"])

if config_dict["noISPyB"]:
    print("No upload to ISPyB or iCAT")
    config_dict["proposal"] = "None"
    config_dict["db"] = -1
else:
    # Check proposal
    # db=0: production
    # db=1: valid
    # db=2: linsvensson
    proposal = UtilsISPyB.getProposal(config_dict["dataDirectory"])
    if proposal is None:
        print(
            "WARNING! No valid proposal could be found for directory {0}.".format(
                config_dict["dataDirectory"]
            )
        )
        print("")
        answer = input("Would you like to enter a valid proposal name now (yes/no)? ")
        while answer != "yes" and answer != "no":
            print("")
            answer = input(
                "Please answer 'yes' or 'no'. Would you like to enter a valid proposal name now? "
            )
        if answer == "yes":
            proposal = input("Please enter a valid proposal name: ")
            code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
            while code is None:
                print("'{0}' is not a valid proposal name.".format(proposal))
                print("")
                proposal = input(
                    "Please enter a valid proposal name (mxXXXX, ih-lsXXXX etc): "
                )
                code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        else:
            proposal = None

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
            db = 1
        else:
            # Use productiond data base
            print("ISPyB production data base used")
            db = 0

    config_dict["proposal"] = proposal
    config_dict["db"] = db

if config_dict["scipionProjectName"] is None:
    config_dict["scipionProjectName"] = "{0}_{1}_{2}".format(
        config_dict["proposal"],
        config_dict["proteinAcronym"],
        config_dict["sampleAcronym"]
    )

user_name = os.getlogin()
celery_worker = config_dict["celery_worker"]

active_workers = celery.current_app.control.inspect().active()

worker_name = "{0}@{1}".format(user_name, celery_worker)
print("Worker name: '{0}'".format(worker_name))
found_worker = False
if active_workers is None:
    print("No active workers!!!")
    sys.exit(1)
else:
    for worker_key, worker_value in active_workers.items():
        print(worker_key)
        if worker_key == worker_name:
            # Check that worker is idle
            if len(worker_value) == 0:
                found_worker = True
                break
            else:
                print("Worker is busy, cannot start job!")
                sys.exit(1)

if found_worker:
    print("Launching processing on worker '{0}' with the following parameters:".format(worker_name))
    for arg_key, arg_value in config_dict.items():
        print("{0:25s}= {1}".format(arg_key, arg_value))
    answer = input("Are you sure? (yes/no): ")
    if answer.lower().startswith("y"):
        app = celery.Celery()
        app.config_from_object("esrf.workflow.celeryconfig")
        future = app.send_task(
            "esrf.workflow.cm_process_worker.run_workflow",
            args=(config_dict,),
            queue=worker_name,
        )
        print("Started!")
        answer = input("Revoke (yes/no)? ")
        if answer == "yes":
            time.sleep(1)
            # app.control.revoke(celery_id)
            future.revoke(terminate=True)
            print("Revoked!")
else:
    print("No worker found!")
