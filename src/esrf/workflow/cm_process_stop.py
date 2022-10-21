import pprint
import sys
import celery


from esrf.workflow.cm_process_status import print_worker_status

app = celery.Celery()
app.config_from_object("esrf.workflow.celeryconfig")

active_workers = celery.current_app.control.inspect().active()
list_processing = print_worker_status(active_workers)
if len(list_processing) == 0:
    print("All workers are idle, nothing to abort.")
    sys.exit(0)
elif len(list_processing) > 1:
    worker_to_abort = input("Which worker do you want to abort? ")
    if worker_to_abort not in active_workers:
        print("No such worker: {0}".format(worker_to_abort))
        sys.exit(1)
else:
    worker_to_abort = list_processing[0]
worker_value = active_workers[worker_to_abort]
for dict_worker in worker_value:
    celery_id = dict_worker["id"]
    list_args = dict_worker["args"]
    for dict_args in list_args:
        for arg_key, arg_value in dict_args.items():
            if arg_key == "dataDirectory":
                directory = arg_value
                break
    are_sure = input(f"Are you sure you want to abort job in {directory}? ")
    if are_sure.lower() != "yes":
        print("Not aborting worker.")
    else:
        celery.current_app.control.revoke(celery_id, terminate=True)
        print(f"Job with celery id {celery_id} aborted.")
