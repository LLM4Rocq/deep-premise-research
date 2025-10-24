"""Step 1: extract raw source files from the configured container."""

import argparse
import os
import json
from dataclasses import asdict
import yaml
from tqdm import tqdm

from src.parser.opam_docker import OpamDocker
from src.config.opam_config import OpamConfig

def extract_sources(config: OpamConfig, new_config_path: str, port: int=8765, kill_clone=False, **_):
    """Dump every `.v` file of the target OPAM packages into JSONL."""
    opam_docker = OpamDocker(config, kill_clone=kill_clone)
    opam_docker.start_pet(port)

    output_sources = config.output + '_sources.jsonl'

    missing_info_path = {}
    for package_name in config.packages:
        try:
            opam_docker.extract_opam_path(package_name, config.info_path)
        except Exception as e:
            missing_info_path[package_name] = ""
    with open(new_config_path, 'w') as file:
        yaml.safe_dump(asdict(config), file, indent=4, sort_keys=False)
    assert not missing_info_path, f"Missing info path for the following packages: {list(missing_info_path.keys())}, add them to the base config file."
    print("Solve all opam packages.")

    try:
        os.remove(output_sources)
    except OSError:
        pass


    for package_name in tqdm(config.packages, desc="Libraries", leave=False):
        lib = opam_docker.extract_files(package_name, config.info_path)
        for filepath in tqdm(lib['subfiles'], desc="Files", position=1, leave=False):
            source = opam_docker.get_source(filepath)
            with open(output_sources, 'a') as file:
                new_entry = {"library": lib, "source": source.to_dict()}
                file.write(json.dumps(new_entry) + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse libraries.")
    parser.add_argument("--config-path", default="config/coq-actuary.yaml", help="Configuration file path")
    parser.add_argument("--new-config-path", default="config/coq-actuary.yaml", help="New configuration file path")
    parser.add_argument("--port", default=8765, type=int, help="Port used for pet-server")
    parser.add_argument("--kill-clone", default=True, type=bool, help="Only authorized one container to be bound to the image.")
    args = parser.parse_args()

    config = OpamConfig.from_yaml(args.config_path)
    extract_sources(config, **vars(args))
