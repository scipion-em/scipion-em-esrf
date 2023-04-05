import os
import socket
import subprocess

user_name = os.getlogin()
host_name = socket.gethostname()
queue_name = "celery." + user_name + "@" + host_name

worker_pid_list = []
try:
    result_binary = subprocess.check_output("pgrep -f -a {0}".format(queue_name).split())
    result = result_binary.decode("utf-8")
    for line in result.split("\n"):
        print(line)
        if "celery" in line:
            worker_pid_list.append(line.split(" ")[0])
except subprocess.CalledProcessError as e:
    pass

if len(worker_pid_list) > 0:
    yesno = input("Are you sure you want to shut down server {0}? (yes/no): ".format(queue_name))
    if yesno.lower() == "yes":
        for pid in worker_pid_list:
            os.system("kill {0}".format(pid))
else:
    print("No worker {0} running on this computer.".format(queue_name))