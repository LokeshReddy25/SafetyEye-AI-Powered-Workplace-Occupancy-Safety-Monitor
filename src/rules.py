"""Violation rule engine.

The dataset has explicit negative classes, so the rules are built on them:
    NO-Hardhat      -> "Missing hardhat"      (on by default)
    NO-Safety Vest  -> "Missing safety vest"  (on by default)
    NO-Mask         -> "Missing mask"         (off by default; enable for sites that require masks)

Each violation detection is associated with the detected `Person` box that contains most of it
(intersection / violation-box area >= `assoc_thresh`). A person with >= 1 violation is non-compliant.
A violation with no matching Person box still counts as one non-compliant worker (the model often
sees a bare head without a full person box).

compliance = compliant workers / all workers in the frame (None when no workers are visible).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional, Sequence

Box = tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels

RULES: dict[str, str] = {
    "NO-Hardhat": "Missing hardhat",
    "NO-Safety Vest": "Missing safety vest",
    "NO-Mask": "Missing mask",
}
DEFAULT_ACTIVE = ("NO-Hardhat", "NO-Safety Vest")


@dataclass(frozen=True)
class Detection:
    cls_name: str
    conf: float
    box: Box


@dataclass
class Violation:
    rule: str            # human-readable, e.g. "Missing hardhat"
    cls_name: str        # dataset class, e.g. "NO-Hardhat"
    conf: float
    box: Box
    person_idx: Optional[int] = None


@dataclass
class FrameResult:
    violations: list[Violation] = field(default_factory=list)
    n_persons: int = 0
    n_workers: int = 0          # persons + violations not attached to any person
    n_noncompliant: int = 0

    @property
    def n_compliant(self) -> int:
        return self.n_workers - self.n_noncompliant

    @property
    def compliance(self) -> Optional[float]:
        return None if self.n_workers == 0 else self.n_compliant / self.n_workers


def intersection_over_a(a: Box, b: Box) -> float:
    """Area(a ∩ b) / Area(a)."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    return 0.0 if area == 0 else ix * iy / area


class RuleEngine:
    def __init__(self, active: Sequence[str] = DEFAULT_ACTIVE, min_conf: float = 0.5,
                 person_min_conf: float = 0.5, assoc_thresh: float = 0.5):
        unknown = set(active) - set(RULES)
        if unknown:
            raise ValueError(f"unknown rule classes: {unknown}")
        self.active = tuple(active)
        self.min_conf = min_conf
        self.person_min_conf = person_min_conf
        self.assoc_thresh = assoc_thresh

    def evaluate(self, detections: Iterable[Detection]) -> FrameResult:
        dets = list(detections)
        persons = [d for d in dets if d.cls_name == "Person" and d.conf >= self.person_min_conf]
        res = FrameResult(n_persons=len(persons))
        flagged_persons: set[int] = set()
        unassigned = 0
        for d in dets:
            if d.cls_name not in self.active or d.conf < self.min_conf:
                continue
            best, best_score = None, 0.0
            for i, p in enumerate(persons):
                s = intersection_over_a(d.box, p.box)
                if s > best_score:
                    best, best_score = i, s
            idx = best if best_score >= self.assoc_thresh else None
            res.violations.append(Violation(RULES[d.cls_name], d.cls_name, d.conf, d.box, idx))
            if idx is None:
                unassigned += 1
            else:
                flagged_persons.add(idx)
        res.n_workers = len(persons) + unassigned
        res.n_noncompliant = len(flagged_persons) + unassigned
        return res


class Cooldown:
    """Allow an event for `key` at most once every `seconds` (prevents alert spam)."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic):
        self.seconds = seconds
        self.clock = clock
        self._last: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        last = self._last.get(key)
        if last is not None and now - last < self.seconds:
            return False
        self._last[key] = now
        return True


def from_ultralytics(result, names: dict[int, str]) -> list[Detection]:
    """Convert one ultralytics Results object to Detection list."""
    b = result.boxes
    if b is None or len(b) == 0:
        return []
    xyxy = b.xyxy.cpu().numpy()
    conf = b.conf.cpu().numpy()
    cls = b.cls.cpu().numpy().astype(int)
    return [Detection(names[c], float(s), tuple(map(float, xy))) for xy, s, c in zip(xyxy, conf, cls)]
