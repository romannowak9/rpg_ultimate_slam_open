#!/usr/bin/env python3

import h5py
import rosbag
import rospy
import numpy as np

from dvs_msgs.msg import EventArray, Event
from sensor_msgs.msg import Imu, Image, CameraInfo
from cv_bridge import CvBridge

import argparse


def convert(h5_path, bag_path):
    print(f"Opening HDF5: {h5_path}")
    f = h5py.File(h5_path, 'r')

    print(f"Creating bag: {bag_path}")
    bag = rosbag.Bag(bag_path, 'w')
    bridge = CvBridge()

    print("Processing events...")

    x = f['/prophesee/left/x']
    y = f['/prophesee/left/y']
    t = f['/prophesee/left/t']
    p = f['/prophesee/left/p']
    idx = f['/prophesee/left/ms_map_idx']

    resolution = f['/prophesee/left/calib/resolution'][:]
    width = int(resolution[0])
    height = int(resolution[1])

    for i in range(len(idx) - 1):
        start = idx[i]
        end = idx[i + 1]

        msg = EventArray()
        msg.events = []

        for j in range(start, end):
            e = Event()
            e.x = int(x[j])
            e.y = int(y[j])
            e.ts = rospy.Time.from_sec(t[j] * 1e-9)
            e.polarity = bool(p[j])
            msg.events.append(e)

        if len(msg.events) == 0:
            continue

        msg.header.stamp = msg.events[0].ts
        msg.header.frame_id = "dvs"
        msg.width = width
        msg.height = height

        bag.write('/dvs/events', msg, msg.header.stamp)

        if i % 1000 == 0:
            print(f"Events batch {i}/{len(idx)}")

    print("Processing IMU...")

    acc = f['/ovc/imu/accel']
    gyro = f['/ovc/imu/omega']
    ts = f['/ovc/imu/ts']

    for i in range(len(ts)):
        msg = Imu()
        msg.header.stamp = rospy.Time.from_sec(ts[i] * 1e-9)
        msg.header.frame_id = "imu"

        msg.linear_acceleration.x = float(acc[i][0])
        msg.linear_acceleration.y = float(acc[i][1])
        msg.linear_acceleration.z = float(acc[i][2])

        msg.angular_velocity.x = float(gyro[i][0])
        msg.angular_velocity.y = float(gyro[i][1])
        msg.angular_velocity.z = float(gyro[i][2])

        bag.write('/dvs/imu', msg, msg.header.stamp)

    print("Processing images...")

    imgs = f['/ovc/left/data']
    ts_img = f['/ovc/ts']

    for i in range(len(ts_img)):
        img = imgs[i][:, :, 0]  # (H, W, 1)

        msg = bridge.cv2_to_imgmsg(img, encoding='mono8')
        msg.header.stamp = rospy.Time.from_sec(ts_img[i] * 1e-9)
        msg.header.frame_id = "camera"

        bag.write('/dvs/image_raw', msg, msg.header.stamp)

        if i % 500 == 0:
            print(f"Images {i}/{len(ts_img)}")

    print("Processing camera info...")

    intrinsics = f['/prophesee/left/calib/intrinsics'][:]
    distortion = f['/prophesee/left/calib/distortion_coeffs'][:]
    resolution = f['/prophesee/left/calib/resolution'][:]

    cam_msg = CameraInfo()
    cam_msg.width = int(resolution[0])
    cam_msg.height = int(resolution[1])

    fx, fy, cx, cy = intrinsics

    cam_msg.K = [fx, 0, cx,
                 0, fy, cy,
                 0, 0, 1]

    cam_msg.D = distortion.tolist()
    cam_msg.header.frame_id = "dvs"

    # zapisujemy kilka razy (jak w normalnych bagach)
    for i in range(10):
        cam_msg.header.stamp = rospy.Time(i)
        bag.write('/dvs/camera_info', cam_msg, cam_msg.header.stamp)

    print("Closing bag...")
    bag.close()
    f.close()

    print("Done!")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("input_h5", help="Path to M3ED .h5 file")
    parser.add_argument("output_bag", help="Output ROS bag file")

    args = parser.parse_args()

    convert(args.input_h5, args.output_bag)
    