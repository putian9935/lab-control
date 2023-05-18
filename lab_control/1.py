#  launch ssh sr_remote1 "C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\Python C:\Users\strontium_remote1\Desktop\1.py --host 0.0.0.0"


import subprocess
def launch(target):
    
def check_python_existence(substr : str):
    proc = subprocess.Popen("ssh", "sr_remote1", "wmic process where " + '"name like ' +
                            "'%python%'" + '" get processid,commandline', stdout=subprocess.PIPE)
    ret = False
    while True:
        l = proc.stdout.readline()
        if substr not in l:
            ret = True 
            break 
        if not l:
            break
    return ret


print(check_python_existence('launch_slave'))