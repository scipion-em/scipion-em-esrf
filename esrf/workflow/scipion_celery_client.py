import json
import time
import celery

from celery import app

#
config_dict = {
    "dataDirectory": "/data/visitor/mx2112/cm01/20220426/RAW_DATA/igm-grid3-2",
    "filesPattern": "Images-Disc1/GridSquare_*/Data/FoilHole_*_fractions.tiff",
    "scipionProjectName": "test_celery_{0}".format(time.time()),
    "proteinAcronym": "igm-fccore",
    "sampleAcronym": "g3",
    "doseInitial": 0.0,
    "magnification": 105000,
    "imagesCount": 40,
    "voltage": 300000,
    "dosePerFrame": 0.935,
    "dataStreaming": True,
    "alignFrame0": 1,
    "alignFrameN": 0,
    "phasePlateData": False,
    "no2dClass": True,
    "onlyISPyB": False,
    "noISPyB": True,
    "particleElimination": False,
    "samplingRate": 0.84,
    "superResolution": True,
    "partSize": 300.0,
    "defectMapPath": None,
    "gainFilePath": None,
    "secondGrid": False,
    "proposal": "mx2112",
    "dataType": 1  # "EPU_TIFF"
}

future = celery.execute.send_task(
        "__main__.run_workflow",
        args=(json.dumps(config_dict),)
    )
print(future)
print(dir(future))
celery_id = future.id
print(celery_id)
print("Started!")
answer = input("Revoke (yes/no)? ")
if answer == "yes":
    time.sleep(1)
    # app.control.revoke(celery_id)
    future.revoke(terminate=True)
    print("Revoked!")
# celery.task.control.revoke(future)
# print(future.get(timeout=10))