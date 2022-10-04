import pprint
import sys
import celery

from cm_process_status import print_worker_status

active_workers = celery.current_app.control.inspect().active()
list_processing = print_worker_status(active_workers)
if len(list_processing) == 0:
    print("All workers are idle, nothing to abort.")
    sys.exit(0)
elif len(list_processing) == 1:
    worker_to_abort = list_processing[0]
    are_sure = input(
        "Are you sure you want to abort worker {0}? ".format(worker_to_abort)
    )
    if are_sure.lower() != "yes":
        print("Not aborting worker.")
        sys.exit(0)
else:
    worker_to_abort = input("Which worker do you want to abort? ")
    if worker_to_abort not in active_workers:
        print("No such worker: {0}".format(worker_to_abort))
        sys.exit(1)
worker_value = active_workers[worker_to_abort]
for dict_worker in worker_value:
    celery_id = dict_worker["id"]
    pprint.pprint(celery_id)
    celery.current_app.control.revoke(celery_id, terminate=True)
    print("Worker {0} aborted.".format(worker_to_abort))
