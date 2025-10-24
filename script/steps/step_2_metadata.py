import argparse
import json
from dataclasses import asdict
from functools import partial
from tqdm import tqdm

from src.config.opam_config import OpamConfig
from src.parser.opam_docker import OpamDocker
from src.parser.tiny_rocq_parser import TinyRocqParser, Source
from script.utils import extract_done, uid_metadata, ram_used_frac, restart_docker, time_limit

def extract_metadata(config: OpamConfig, port: int=8765, kill_clone=False, toc_timeout=5*60, extract_timeout=2*60, max_memory=0.8, **_):
    opam_docker = OpamDocker(config, kill_clone=kill_clone)
    opam_docker.start_pet(port)
    tiny_parser = TinyRocqParser(port)

    output_sources = config.output + '_sources.jsonl' 
    output_metadata = config.output + '_metadata.jsonl'
    
    done = extract_done(uid_metadata, output_metadata)

    sources_file = open(output_sources, 'r')
    for line in tqdm(sources_file.readlines()):
        entry = json.loads(line)
        library = entry['library']
        source = Source.from_dict(entry['source'])
        filepath = source.path
        if ram_used_frac() > max_memory:
            print("Reset memory")
            opam_docker = restart_docker(opam_docker, config, port, kill_clone=kill_clone)
        
        if filepath in done:
            continue
        try:
            with time_limit(toc_timeout, "extract_proof"):
                theorems = tiny_parser.extract_toc(source)

            with time_limit(extract_timeout, "extract_proof"):
                if theorems:
                    loadpath, dependencies = tiny_parser.extract_dependencies(source, theorems)
                    new_entry = {"library": library, "source": source.to_dict(), "loadpath": loadpath, "dependencies": dependencies, "theorems": [asdict(thm) for thm in theorems]}
                    with open(output_metadata, 'a') as file:
                        file.write(json.dumps(new_entry) + "\n")
        except Exception as e:
            print(f"WARNING: {e}")
            opam_docker = restart_docker(opam_docker, config, port, kill_clone=kill_clone)
            continue

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse libraries.")
    parser.add_argument("--config-path", default="config/coq-actuary.yaml", help="Config file for extraction")
    parser.add_argument("--port", default=8765, type=int, help="Port used for pet-server")
    parser.add_argument("--max_memory", default=0.80, type=float)    
    parser.add_argument("--toc-timeout", default=5*60, type=int)
    parser.add_argument("--extract-timeout", default=2*60, type=int)
    parser.add_argument("--kill-clone", default=False, type=bool)
    args = parser.parse_args()

    config = OpamConfig.from_yaml(args.config_path)
    extract_metadata(config, **vars(args))
