"""Step 3: replay proofs to capture goals, steps, and dependencies."""

import argparse
import json
from dataclasses import asdict
from tqdm import tqdm

from src.config.opam_config import OpamConfig
from src.parser.opam_docker import OpamDocker
from src.parser.tiny_rocq_parser import TinyRocqParser, Element, Source
from script.utils import extract_done, uid_theorem, ram_used_frac, restart_docker, time_limit

def extract_elements(config: OpamConfig, port: int=8765, kill_clone=False, extract_timeout=2*60, max_memory=0.8, **_):
    """Replay proofs for each theorem and capture all proof steps."""
    opam_docker = OpamDocker(config, kill_clone=kill_clone)
    opam_docker.start_pet(port)
    tiny_parser = TinyRocqParser(port)

    output_elements = config.output + '_elements.jsonl' 
    output_metadata = config.output + '_metadata.jsonl'
    
    done = extract_done(uid_theorem, output_elements)

    sources_file = open(output_metadata, 'r')
    for line in tqdm(sources_file.readlines()):
        entry = json.loads(line)
        theorems = [Element.from_dict(thm) for thm in entry['theorems']]
        source = Source.from_dict(entry['source'])
        library = entry['library']
        for theorem in tqdm(theorems, desc="Elements", position=1, leave=False):
            if ram_used_frac() > max_memory:
                print("RESET MEMORY")
                opam_docker = restart_docker(opam_docker, config, port, kill_clone=kill_clone)
            if uid_theorem(theorem) in done:
                continue
            try:
                with time_limit(extract_timeout, "extract_proof"):
                    steps = tiny_parser(theorem, source)
                    new_entry = {"library": library, "theorem": asdict(theorem), "steps": [asdict(step) for step in steps]}
                    with open(output_elements, 'a') as file:
                        file.write(json.dumps(new_entry) + "\n")
            except Exception as e:
                print(f"WARNING: {e}")
                opam_docker = restart_docker(opam_docker, config, port)
                continue

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse libraries.")
    parser.add_argument("--config-path", default="config/coq-actuary.yaml", help="Config file for extraction")
    parser.add_argument("--port", default=8765, type=int, help="Port used for pet-server")
    parser.add_argument("--max_memory", default=0.80, type=float)    
    parser.add_argument("--extract-timeout", default=2*60, type=int)
    parser.add_argument("--kill-clone", default=False, type=bool)
    args = parser.parse_args()

    config = OpamConfig.from_yaml(args.config_path)
    extract_elements(config, **vars(args))
