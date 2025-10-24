from dataclasses import dataclass, field
from typing import Dict

import yaml

@dataclass
class OpamConfig:
    name: str
    output: str
    tag: str
    packages: list[str]
    base_image: str
    opam_env_path: str
    user: str
    info_path: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "OpamConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)