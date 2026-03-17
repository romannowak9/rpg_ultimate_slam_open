# Instruction of run Ultimate SLAM

Only for my personal use.

## How to run docker?

To rebuild run:
```bash
cd docker
sh build.sh ~/.ssh/id_rsa
```

To launch container run from root:
```bash
./launch_container /mnt/docker_disk/home/mgr/datasets
```

In **VSCode** `Ctrl+Shift+P` -> `Attach to running container` -> `uslam`

## How to run USLAM with example data?

```bash
source ~/uslam_ws/devel/setup.bash
```

Events + IMU
```bash
roslaunch ze_vio_ceres ijrr17_events_only.launch bag_filename:=<path_to_bag_file>
```
Events + IMU + Frames
```bash
roslaunch ze_vio_ceres ijrr17.launch bag_filename:=<path_to_bag_file>
```

For example:
```bash
roslaunch ze_vio_ceres ijrr17_events_only.launch bag_filename:=/data/uSLAM/boxes_6dof.bag  
```
