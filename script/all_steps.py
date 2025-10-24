"""Command-line entry point that runs every extraction stage in order."""

import argparse
import os

from tqdm import tqdm

from src.config.opam_config import OpamConfig
from script.steps.step_0_docker import build_image
from script.steps.step_1_sources import extract_sources
from script.steps.step_2_metadata import extract_metadata
from script.steps.step_3_elements import extract_elements

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build docker image")
    parser.add_argument("--config-path", default="config/", help="Configuration file path")
    parser.add_argument("--rebuild", default=False, help="Ignore if image already exists")
    parser.add_argument("--port", default=8765, type=int, help="Port used for pet-server")
    parser.add_argument("--max_memory", default=0.80, type=float)    
    parser.add_argument("--toc-timeout", default=5*60, type=int)
    parser.add_argument("--extract-timeout", default=2*60, type=int)
    parser.add_argument("--kill-clone", default=False, type=bool)
    args = parser.parse_args()

    all_configs = []
    for config_filename in os.listdir(args.config_path):
        config_path = os.path.join(args.config_path, config_filename)
        all_configs.append(OpamConfig.from_yaml(config_path))
    
    for config in tqdm(all_configs, desc="Building All Docker Images"):
        try:
            build_image(config, **vars(args))
        except Exception as e:
            print(f"ignore {config.name}")

    for config in tqdm(all_configs, desc="Extracting All Sources"):
        try:
            extract_sources(config, **vars(args))
        except Exception as e:
            print(f"ignore {config.name}")
        
    
    for config in tqdm(all_configs, desc="Extracting All Metadata"):
        try:
            extract_metadata(config, **vars(args))
        except Exception as e:
            print(f"ignore {config.name}")

    for config in tqdm(all_configs, desc="Extracting All Elements"):
        try:
            extract_elements(config, **vars(args))
        except Exception as e:
            print(f"ignore {config.name}")
