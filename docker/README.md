# Docker installation

The Dockerfile image in this folder provides USLAM pre-installed and iniVation dv-ros driver.

### Dependencies

1. Install docker: https://docs.docker.com/engine/install/ubuntu/
    ```
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```
3. Docker post installation steps: https://docs.docker.com/engine/install/linux-postinstall/ 
   1. Summarized: 
      - `sudo groupadd docker`
      - `sudo usermod -aG docker $USER`
      - `newgrp docker`
   2. Open another shell and check that everything worked out: `docker run hello-world`

### Build docker image
To build the Docker image, run: 

    cd docker
    sh build.sh GITHUB_SSH_KEY
    
    
where `GITHUB_SSH_KEY` is the path to the ssh key that allows you to clone repositories from GitHub (eg. `~/.ssh/id_rsa`).

Not sure which key to use? Run `ssh -vT git@github.com` and search for the line starting with `Server accepts key: ...`.

### Use the docker image

To use the docker container, run:
    
    ./launch_container /path/to/your/data
    
where `/path/to/your/data` is the path to the folder containing the data you might want to use USLAM with.

#### Running the Live Demo

To run the live demo, check out [this instructions](../docs/Run-Live-Demo.md), following the
steps for the iniVation dv-ros driver (provided in the image).

Use the `./launch_container` command above to start the container. To open an additional terminal in the container (as
suggested in the live demo instructions), run:
    
    ./attach_container
    
