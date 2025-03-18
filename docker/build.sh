if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_github_private_key>"
    exit 1
fi

eval "$(ssh-agent -s)"
ssh-add $1
# Here we cd .. to include the root of the project in the build context, so that the Dockerfile can access the files
cd .. && DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t rpg/ultimate_slam_open:melodic --build-arg UID=$(id -u) --build-arg GID=$(id -g) .
