import os

# os.popen('pythonw cam_main.py').read()
import subprocess

t= subprocess.call('python cam_main.py', shell=True)


