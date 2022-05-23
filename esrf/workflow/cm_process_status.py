import pprint
import datetime
import celery

# pprint.pprint(celery.current_app.control.inspect().stats())

active_workers = celery.current_app.control.inspect().active()
if active_workers is None:
    print("No active workers!!!")
else:
    for worker_key, worker_value in active_workers.items():
        if len(worker_value) == 0:
            print("Worker: {0:20s} Status: Idle".format(worker_key))
        else:
            print("Worker: {0:20s} Status: Processing".format(worker_key))
            # pprint.pprint(worker_value)
            for dict_worker in worker_value:
                time_start = datetime.datetime.fromtimestamp(dict_worker["time_start"])
                date_time_str = time_start.strftime("%Y-%m-%d %H:%M:%S")
                print("Start time: {0}".format(date_time_str))
                list_args = dict_worker["args"]
                for dict_args in list_args:
                    for arg_key, arg_value in dict_args.items():
                        print("{0:25s}= {1}".format(arg_key, arg_value))

        print()
