# CreateVMPython
Python script for creating virtual machines on Ubuntu using virsh

- First of all, this script runs on Ubuntu using python3 and it needs two files: plantilla-vm-pf1.xml (in this repository) and cdps-vm-base-pf1.qcow2 (you can download it from here: https://mega.nz/#!UgtgiIxB!8zmmvFWnKMSAwlK6Ym6-GzhdHdSjFuEKUXsruVfDQc8 )
- Also, it is necessary to install virsh: sudo apt-get install libvirt-bin 

- This script is simple, it creates a setting of a network composed of the host and the VMs (c1, lb and 1-5 servers).
- All the files needed will be created in the folder /mnt/tmp/.
- Create: python3 pf1.py crear <optional> (This optional is a number between 1-5, if its empty, the default number of servers will be 2)
- Start: python3 pf1.py arrancar <optional> (This optional is the number of the server you want to start, if its empty, all of them will initialiate)
- Pause: python3 pf1.py parar <optional> (This optional is the number of the server you want to pause, if its empty, all of them will stop)
- Monitor (check the status of the VMs): python pf1.py monitor
- Destroy (It destroy all the VMs and delete all the generated file): python3 pf1.py destroy
