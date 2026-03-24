#!/usr/bin/env python3

import h5py
import rosbag
import rospy
import numpy as np

from dvs_msgs.msg import EventArray, Event
from sensor_msgs.msg import Imu, Image, CameraInfo
from cv_bridge import CvBridge

import argparse

EVENT_CHUNK = 100000  # liczba eventów w jednej wiadomości ROS


def convert_events(f, bag):
    print("Preparing event datasets...")

    x = f['/prophesee/left/x']
    y = f['/prophesee/left/y']
    t = f['/prophesee/left/t']
    p = f['/prophesee/left/p']

    resolution = f['/prophesee/left/calib/resolution'][:]
    width, height = int(resolution[0]), int(resolution[1])

    total_events = len(x)
    print("Total events:", total_events)

    # przetwarzanie w blokach
    for start in range(0, total_events, EVENT_CHUNK):
        end = min(start + EVENT_CHUNK, total_events)

        xs = x[start:end].astype(np.int16)
        ys = y[start:end].astype(np.int16)
        ts = t[start:end].astype(np.float64) * 1e-9  # konwersja do sekund
        ps = p[start:end].astype(bool)

        msg = EventArray()
        msg.header.frame_id = "dvs"
        msg.header.stamp = rospy.Time.from_sec(ts[0])
        msg.width = width
        msg.height = height

        # tworzenie Eventów w liście (tak jak w oryginale)
        msg.events = [Event(x=int(xi), y=int(yi), ts=rospy.Time.from_sec(ti), polarity=pi)
                      for xi, yi, ti, pi in zip(xs, ys, ts, ps)]

        bag.write('/dvs/events', msg, msg.header.stamp)

        if start % (EVENT_CHUNK) == 0:
            print(f"Events processed: {start/total_events*100}%")


def convert_imu(f, bag):
    print("Processing IMU...")

    acc = f['/ovc/imu/accel']
    gyro = f['/ovc/imu/omega']
    ts = f['/ovc/imu/ts']

    total = len(ts)

    acc_np = np.array(acc, dtype=np.float64)
    gyro_np = np.array(gyro, dtype=np.float64)
    ts_np = np.array(ts, dtype=np.float64) * 1e-9

    for i in range(total):
        msg = Imu()
        msg.header.stamp = rospy.Time.from_sec(ts_np[i])
        msg.header.frame_id = "imu"

        msg.linear_acceleration.x = float(acc_np[i][0])
        msg.linear_acceleration.y = float(acc_np[i][1])
        msg.linear_acceleration.z = float(acc_np[i][2])

        msg.angular_velocity.x = float(gyro_np[i][0])
        msg.angular_velocity.y = float(gyro_np[i][1])
        msg.angular_velocity.z = float(gyro_np[i][2])

        bag.write('/dvs/imu', msg, msg.header.stamp)


def convert_images(f, bag):
    print("Processing images...")
    bridge = CvBridge()

    imgs = f['/ovc/left/data']
    ts = f['/ovc/ts']

    total = len(ts)

    for i in range(total):
        # pobranie monochromatycznego kanału
        img = np.array(imgs[i][:, :, 0], dtype=np.uint8)

        msg = bridge.cv2_to_imgmsg(img, encoding='mono8')
        msg.header.stamp = rospy.Time.from_sec(ts[i] * 1e-9)
        msg.header.frame_id = "camera"

        bag.write('/dvs/image_raw', msg, msg.header.stamp)

        if i % 200 == 0:
            print(f"Images processed: {i}/{total}")


def convert_camera_info(f, bag):
    print("Processing camera info...")

    intrinsics = f['/prophesee/left/calib/intrinsics'][:]
    distortion = f['/prophesee/left/calib/distortion_coeffs'][:]
    resolution = f['/prophesee/left/calib/resolution'][:]

    width, height = int(resolution[0]), int(resolution[1])
    fx, fy, cx, cy = intrinsics

    cam = CameraInfo()
    cam.width = width
    cam.height = height
    cam.K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
    cam.D = distortion.tolist()
    cam.header.frame_id = "dvs"

    # tak jak w oryginale: 10 wpisów
    for i in range(10):
        cam.header.stamp = rospy.Time(i)
        bag.write('/dvs/camera_info', cam, cam.header.stamp)


def convert(h5_path, bag_path):
    print("Opening HDF5:", h5_path)
    f = h5py.File(h5_path, 'r')

    print("Creating bag:", bag_path)
    bag = rosbag.Bag(bag_path, 'w')

    convert_events(f, bag)
    convert_imu(f, bag)
    convert_images(f, bag)
    convert_camera_info(f, bag)

    bag.close()
    f.close()
    print("Finished conversion.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_h5")
    parser.add_argument("output_bag")
    args = parser.parse_args()

    convert(args.input_h5, args.output_bag)
    