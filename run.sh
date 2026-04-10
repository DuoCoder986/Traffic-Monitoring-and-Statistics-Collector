#!/bin/bash
# -------------------------------------------------------------
# SDN Project Setup Script (POX Version)
# Automatically clones POX, loads the controller, and starts Mininet
# -------------------------------------------------------------

echo "--------------------------------------------------------"
echo "Cleaning up past Mininet / OVS environments..."
echo "--------------------------------------------------------"
sudo mn -c 2>/dev/null

echo "--------------------------------------------------------"
echo "Checking for POX installation..."
echo "--------------------------------------------------------"
if [ ! -d "pox" ]; then
    echo "POX is not installed. Cloning from github..."
    git clone https://github.com/noxrepo/pox.git
else
    echo "POX is already installed in this directory."
fi

echo "--------------------------------------------------------"
echo "Deploying custom controller module to POX..."
echo "--------------------------------------------------------"
# In POX, external modules are placed in the 'ext' directory.
cp controller.py pox/ext/custom_controller.py
echo "Copied controller.py to pox/ext/custom_controller.py"

echo "--------------------------------------------------------"
echo "Starting the POX Controller in the background..."
echo "--------------------------------------------------------"
# We use xterm to open a new window for the POX controller to easily see its output.
# If xterm is missing, you can install it via 'sudo apt install xterm'.
# Note: running POX using python3.
if command -v xterm &> /dev/null; then
    xterm -T "POX Controller" -e "python3 ./pox/pox.py log.level --DEBUG ext.custom_controller" &
    echo "Controller started in a new xterm window."
else
    echo "[WARNING] xterm is not installed. Running controller in the background..."
    echo "> To see controller logs, run 'python3 ./pox/pox.py log.level --DEBUG ext.custom_controller' in a separate terminal."
    nohup python3 ./pox/pox.py log.level --DEBUG ext.custom_controller > pox_output.log 2>&1 &
fi

sleep 3 # wait for controller to start

echo "--------------------------------------------------------"
echo "Starting Mininet Custom Topology..."
echo "--------------------------------------------------------"
# Starting Mininet. Note that POX defaults to OpenFlow 1.0 natively, so we don't force OpenFlow13.
sudo mn --custom topology.py --topo custom --controller remote,ip=127.0.0.1,port=6633 --switch ovsk --mac
