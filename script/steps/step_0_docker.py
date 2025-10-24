"""Step 0: build Docker images for each OPAM configuration."""

import argparse

import docker

from src.config.opam_config import OpamConfig
from src.parser.opam_docker import OpamDocker

def build_image(config: OpamConfig, rebuild: bool=False, **_):
    """Create a container image for the requested packages if needed."""
    client = docker.from_env()
    new_image_name = config.name + ":" + config.tag
    filterred_images = client.images.list(filters={'reference': new_image_name})
    if filterred_images and not rebuild:
        print('Image already exists')
        return
    opam_docker = OpamDocker(config, build=True)
    opam_docker.install_project(" ".join(config.packages))
    opam_docker.container.commit(config.name, config.tag)
    opam_docker.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build docker image")
    parser.add_argument("--config-path", default="config/coq-actuary.yaml", help="Configuration file path")
    parser.add_argument("--rebuild", default=False, help="If True: build image even if it already exists.")
    args = parser.parse_args()

    config = OpamConfig.from_yaml(args.config_path)

    build_image(config, **vars(args))
