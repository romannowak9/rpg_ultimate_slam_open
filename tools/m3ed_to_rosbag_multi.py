#!/usr/bin/env python3
import h5py
import rosbag
import rospy
import numpy as np
from dvs_msgs.msg import EventArray, Event
from sensor_msgs.msg import Imu, Image, CameraInfo
from cv_bridge import CvBridge
import argparse
from numba import njit
import multiprocessing as mp
import os

# Maksymalna liczba eventów w jednym wpisie
EVENT_CHUNK = 1_000_000  # 1 mln eventów na EventArray

@njit
def create_events_numba(xs, ys, ts, ps):
    n = len(xs)
    out_x = np.zeros(n, np.int16)
    out_y = np.zeros(n, np.int16)
    out_ts = np.zeros(n, np.float64)
    out_p = np.zeros(n, np.bool_)
    for i in range(n):
        out_x[i] = xs[i]
        out_y[i] = ys[i]
        out_ts[i] = ts[i]
        out_p[i] = ps[i]
    return out_x, out_y, out_ts, out_p

def worker_events(h5_path, start_idx, end_idx, tmp_bag_path):
    f = h5py.File(h5_path, 'r')
    x = f['/prophesee/left/x']
    y = f['/prophesee/left/y']
    t = f['/prophesee/left/t']
    p = f['/prophesee/left/p']
    resolution = f['/prophesee/left/calib/resolution'][:]
    width, height = int(resolution[0]), int(resolution[1])

    bag = rosbag.Bag(tmp_bag_path, 'w')

    for start in range(start_idx, end_idx, EVENT_CHUNK):
        chunk_end = min(start + EVENT_CHUNK, end_idx)
        xs = np.array(x[start:chunk_end], dtype=np.int16)
        ys = np.array(y[start:chunk_end], dtype=np.int16)
        ts = np.array(t[start:chunk_end], dtype=np.float64) * 1e-9
        ps = np.array(p[start:chunk_end], dtype=np.bool_)

        xs, ys, ts, ps = create_events_numba(xs, ys, ts, ps)

        msg = EventArray()
        msg.header.frame_id = "dvs"
        msg.header.stamp = rospy.Time.from_sec(ts[0])
        msg.width = width
        msg.height = height
        msg.events = [Event(x=int(xs[i]), y=int(ys[i]),
                            ts=rospy.Time.from_sec(ts[i]), polarity=ps[i])
                      for i in range(len(xs))]
        bag.write('/dvs/events', msg, msg.header.stamp)

        if start % (EVENT_CHUNK) == 0:
            print(f"[Process {os.getpid()}] Events processed: {(start-start_idx)/(end_idx-start_idx)*100}%")

    bag.close()
    f.close()

def merge_bags(output_path, tmp_paths):
    os.system("rosbag reindex " + " ".join(tmp_paths))  # reindex tmp bags
    os.system("rosbag merge -o {} {}".format(output_path, " ".join(tmp_paths)))
    for p in tmp_paths:
        os.remove(p)

# --- IMU, obrazy, CameraInfo przetwarzamy w głównym procesie ---
def convert_imu(f, bag):
    print("Processing IMU...")
    acc = np.array(f['/ovc/imu/accel'], dtype=np.float64)
    gyro = np.array(f['/ovc/imu/omega'], dtype=np.float64)
    ts = np.array(f['/ovc/imu/ts'], dtype=np.float64) * 1e-9
    total = len(ts)
    for i in range(total):
        msg = Imu()
        msg.header.stamp = rospy.Time.from_sec(ts[i])
        msg.header.frame_id = "imu"
        msg.linear_acceleration.x = float(acc[i][0])
        msg.linear_acceleration.y = float(acc[i][1])
        msg.linear_acceleration.z = float(acc[i][2])
        msg.angular_velocity.x = float(gyro[i][0])
        msg.angular_velocity.y = float(gyro[i][1])
        msg.angular_velocity.z = float(gyro[i][2])
        bag.write('/dvs/imu', msg, msg.header.stamp)

def convert_images(f, bag):
    print("Processing images...")
    bridge = CvBridge()
    imgs = f['/ovc/left/data']
    ts = np.array(f['/ovc/ts'], dtype=np.float64) * 1e-9
    total = len(ts)
    for i in range(total):
        img = np.array(imgs[i][:, :, 0], dtype=np.uint8)
        msg = bridge.cv2_to_imgmsg(img, encoding='mono8')
        msg.header.stamp = rospy.Time.from_sec(ts[i])
        msg.header.frame_id = "camera"
        bag.write('/dvs/image_raw', msg, msg.header.stamp)
        if i % 10 == 0:
            print(f"Images processed: ({(i/total) * 100}%")

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
    for i in range(10):
        cam.header.stamp = rospy.Time(i)
        bag.write('/dvs/camera_info', cam, cam.header.stamp)

def convert(h5_path, bag_path, n_processes=4):
    f = h5py.File(h5_path, 'r')
    total_events = len(f['/prophesee/left/x'])
    print(f"Total events: {total_events}")

    # --- multiprocesing eventów ---
    chunk_size = total_events // n_processes
    tmp_paths = []
    processes = []

    for i in range(n_processes):
        start_idx = i * chunk_size
        end_idx = total_events if i == n_processes-1 else (i+1)*chunk_size
        tmp_bag = f"{bag_path}.tmp_{i}.bag"
        tmp_paths.append(tmp_bag)
        p = mp.Process(target=worker_events, args=(h5_path, start_idx, end_idx, tmp_bag))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # --- scalanie tmp bagów ---
    merge_bags(bag_path, tmp_paths)

    # --- przetwarzanie IMU, obrazów, CameraInfo ---
    bag = rosbag.Bag(bag_path, 'a')  # dopisanie
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
    parser.add_argument("--processes", type=int, default=4, help="Number of parallel processes")
    args = parser.parse_args()
    convert(args.input_h5, args.output_bag, n_processes=args.processes)