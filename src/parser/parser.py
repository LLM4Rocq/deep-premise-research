from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, asdict

from typing import Tuple, List, Dict, Optional, Any

@dataclass
class Position:
    line: int
    character: int

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Position":
        return cls(line=int(d["line"]), character=int(d["character"]))

@dataclass
class Range:
    start: Position
    end: Position

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Range":
        return cls(start=Position.from_dict(d["start"]),
                   end=Position.from_dict(d["end"]))

@dataclass
class Element:
    origin: str
    name: str
    statement: str
    range: Range

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Element":
        return cls(
            origin=d["origin"],
            name=d["name"],
            statement=d["statement"],
            range=Range.from_dict(d["range"]),
        )

@dataclass
class Dependency:
    origin: str
    name: str
    range: Range
    kind: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Dependency":
        return cls(
            origin=d["origin"],
            name=d["name"],
            range=Range.from_dict(d["range"]),
            kind=d["kind"],
        )

@dataclass
class Step:
    step: str
    state_in: Any
    state_out: Any
    dependencies: List[Dependency]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Step":
        return cls(
            step=d["step"],
            state_in=d["state_in"],
            state_out=d["state_out"],
            dependencies=[Dependency.from_dict(x) for x in d["dependencies"]],
        )

@dataclass
class Source:
    path: Path
    content: str
    @property
    def content_lines(self) -> List[str]:
        return self.content.splitlines()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["path"] = str(d["path"])
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Source":
        p = d.get("path")
        return cls(
            path=p if isinstance(p, Path) else Path(p),
            content=d["content"],
        )

class ProofNotFound(Exception):
    pass

class TimeOut(Exception):
    pass

def update_statement(theorem: Element, source: Source):
    try:
        lines = source.content_lines[theorem.range.start.line: theorem.range.end.line+1]
        lines[0] = lines[0][theorem.range.start.character:]
        lines[-1] = lines[-1][:theorem.range.end.character]
        theorem.statement = "\n".join(lines)
    except IndexError:
        print(f"Failed to extract statement from {theorem} in {source.path}")

class AbstractParser(ABC):

    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def __call__(self, theorem: Element, source: Source) -> List[Step]:
        pass