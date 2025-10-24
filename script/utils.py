import signal
from contextlib import contextmanager
from typing import List, Dict, Any, Union
from collections.abc import Callable
import json
import os
import psutil
import gc
import time


from src.parser.opam_docker import OpamDocker
from src.parser.parser import Element, Source

@contextmanager
def time_limit(seconds, name="call"):
    def _handler(signum, frame):
        raise TimeoutError(f"{name} timed out after {seconds}s")
    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)

def uid_theorem(theorem: Union[Dict, Element]) -> str:
    if isinstance(theorem, Element):
        return theorem.statement + str(theorem.range.start.line)
    else:
        return theorem['theorem']['statement'] + str(theorem['theorem']['range']['start']['line'])

def uid_source(source: Union[Dict, Source]) -> str:
    if isinstance(source, Source):
        return source.path
    else:
        return source['source']['path']

def uid_metadata(source: Dict) -> str:
    return source['source']

def extract_done(uid_generator: Callable[[Dict], str], output: str) -> Dict[str, Dict]:
    done = {}
    if not os.path.exists(output):
        return done
    with open(output, 'r') as file:
        for line in file.readlines():
            entry = json.loads(line)
            uid = uid_generator(entry)
            assert uid not in done, f"Collision with {output}: {uid} already known"
            done[uid] = entry
    return done

def is_done(uid_generator: Callable[[Dict], str], obj: Dict, done: Dict[str, Dict]) -> bool:
    return uid_generator(obj) in done

def ram_used_frac() -> float:
    vm = psutil.virtual_memory()
    return vm.used / vm.total

def restart_docker(opam_docker, config, port, kill_clone=False):
    try:
        opam_docker.close()
    except Exception:
        pass
    gc.collect()
    time.sleep(0.25)
    opam_docker = OpamDocker(config, kill_clone=kill_clone)
    opam_docker.start_pet(port)
    return opam_docker
