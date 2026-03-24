FROM ubuntu:18.04

ENV USERNAME rpg
ARG UID=1000
ARG GID=1000

ENV HOME /home/$USERNAME

# Create user
RUN apt-get update && \
      apt-get -y install sudo
RUN useradd -m $USERNAME && \
    echo "$USERNAME:$USERNAME" | chpasswd && \
    usermod --shell /bin/bash $USERNAME && \
    usermod -aG sudo $USERNAME && \
    mkdir -p /etc/sudoers.d && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    usermod  --uid $UID $USERNAME && \
    groupmod --gid $GID $USERNAME && \
    usermod -a -G tty $USERNAME && \
    usermod -a -G dialout $USERNAME

RUN mkdir /.local
RUN chmod 777 /.local
RUN mkdir /.config
RUN chmod 777 /.config

# Install dependencies
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && \
    apt-get install -y \
    curl \
    build-essential \
    lsb-release \
    cmake \
    git \
    expect \
    openssh-client \
    liblapack-dev \
    libblas-dev \
    vim \
    wget \
    autoconf \
    automake \
    libtool \
    python3-venv

RUN apt install -y \
    python3-pip \
    python3-yaml

RUN mkdir -p -m 0600 /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts

# Install ROS Noetic
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y ros-melodic-desktop-full python-catkin-tools python-vcstool ros-melodic-vrpn ros-melodic-vrpn-client-ros

# Install Ultimate SLAM workspace
COPY ./ /uslam_ws/src/rpg_ultimate_slam_open/
RUN --mount=type=ssh  mkdir -p /uslam_ws/src && cd /uslam_ws && \
    catkin config --extend /opt/ros/melodic --cmake-args -DCMAKE_BUILD_TYPE=Release && \
    cd /uslam_ws/src && vcs-import < rpg_ultimate_slam_open/dependencies.yaml && \
    catkin build ze_vio_ceres

COPY docker/setupros.bash /home/${USERNAME}/setupros.bash
RUN echo "source /home/${USERNAME}/setupros.bash" >> /home/${USERNAME}/.bashrc
