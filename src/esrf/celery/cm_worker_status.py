import celery
import datetime


def print_worker_status(active_workers):
    list_processing = []
    if active_workers is None:
        print("No active workers!!!")
    else:
        for worker_key, worker_value in active_workers.items():
            print("")
            if len(worker_value) == 0:
                print("Worker: {0:20s} Status: Idle".format(worker_key))
            else:
                print("Worker: {0:20s} Status: Processing".format(worker_key))
                list_processing.append(worker_key)
                for dict_worker in worker_value:
                    print("")
                    print("")
                    time_start = datetime.datetime.fromtimestamp(
                        dict_worker["time_start"]
                    )
                    date_time_str = time_start.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Start time: {date_time_str}")
                    celery_id = dict_worker["id"]
                    print(f"Celery id: {celery_id}")
                    list_args = dict_worker["args"]
                    for dict_args in list_args:
                        for arg_key, arg_value in dict_args.items():
                            print("{0:25s}= {1}".format(arg_key, arg_value))
            print()
    return list_processing

if __name__ == "__main__":
    print("Checking status of CM celery workers...")
    app = celery.Celery()
    app.config_from_object("esrf.celery.cm_config")
    active_workers = celery.current_app.control.inspect().active()
    # print(f"Active workers: {active_workers}")
    list_processing = print_worker_status(active_workers)
