#!/usr/bin/env python3

import rosbag
import rospy
from dvs_msgs.msg import EventArray, Event
from sensor_msgs.msg import Imu, Image, CameraInfo
from cv_bridge import CvBridge
import h5py
import numpy as np

print('XD')