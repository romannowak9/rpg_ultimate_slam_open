#!/bin/bash
unset my_ip
export ROS_VERSION=melodic
export CATKIN_WS=/uslam_ws

source /opt/ros/${ROS_VERSION}/setup.sh
source $CATKIN_WS/devel/setup.bash

my_ip=$(hostname -I | sed 's/\([0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\).*/\1/g')

if [ -z "$my_ip" ]
then
  my_ip=127.0.0.1
fi
roscore_ip=$my_ip

echo "ROS Workspace is ""$CATKIN_WS"
echo "IP Address is ""$my_ip"
echo "MASTER IP Address is ""$roscore_ip"

export ROS_IP=$my_ip
export ROS_HOSTNAME=$my_ip
export ROS_MASTER_URI=http://${roscore_ip}:11311
