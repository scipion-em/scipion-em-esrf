import json
import time
import celery

from celery import app


future = celery.execute.send_task(
        "__main__.revoke_tst",
        args=()
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