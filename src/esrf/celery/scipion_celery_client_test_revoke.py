import json
import time
import celery
input_data = {}
from celery import app
worker_name = "svensson@cmproc3"
app = celery.Celery()
app.config_from_object("esrf.celery.cm_config")
future = app.send_task(
    "esrf.sp.cm_process_worker.revoke_tst",
    args=({"input_data": False},),
    queue=worker_name
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
