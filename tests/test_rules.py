import pytest

from src.rules import Cooldown, Detection, RuleEngine, intersection_over_a

PERSON = Detection("Person", 0.9, (100, 100, 200, 400))
HEAD_NO_HAT = Detection("NO-Hardhat", 0.8, (130, 100, 170, 140))      # inside person
NO_VEST = Detection("NO-Safety Vest", 0.7, (110, 150, 190, 260))      # inside person
HARDHAT = Detection("Hardhat", 0.9, (130, 100, 170, 140))


def test_compliant_person():
    r = RuleEngine().evaluate([PERSON, HARDHAT, Detection("Safety Vest", 0.8, (110, 150, 190, 260))])
    assert r.violations == [] and r.n_workers == 1 and r.compliance == 1.0


def test_missing_helmet_is_violation_and_attached_to_person():
    r = RuleEngine().evaluate([PERSON, HEAD_NO_HAT])
    assert [v.rule for v in r.violations] == ["Missing hardhat"]
    assert r.violations[0].person_idx == 0
    assert r.n_workers == 1 and r.n_noncompliant == 1 and r.compliance == 0.0


def test_two_violations_same_person_count_once():
    r = RuleEngine().evaluate([PERSON, HEAD_NO_HAT, NO_VEST])
    assert len(r.violations) == 2 and r.n_noncompliant == 1 and r.n_workers == 1


def test_violation_without_person_box_counts_as_worker():
    r = RuleEngine().evaluate([HEAD_NO_HAT])
    assert r.n_persons == 0 and r.n_workers == 1 and r.compliance == 0.0
    assert r.violations[0].person_idx is None


def test_mixed_scene_compliance():
    p2 = Detection("Person", 0.9, (300, 100, 400, 400))
    r = RuleEngine().evaluate([PERSON, p2, HEAD_NO_HAT])
    assert r.n_workers == 2 and r.compliance == 0.5


def test_low_confidence_ignored():
    r = RuleEngine(min_conf=0.5).evaluate([PERSON, Detection("NO-Hardhat", 0.3, HEAD_NO_HAT.box)])
    assert r.violations == [] and r.compliance == 1.0


def test_mask_rule_off_by_default_and_configurable():
    no_mask = Detection("NO-Mask", 0.9, (140, 115, 160, 135))
    assert RuleEngine().evaluate([PERSON, no_mask]).violations == []
    r = RuleEngine(active=("NO-Mask",)).evaluate([PERSON, no_mask])
    assert [v.rule for v in r.violations] == ["Missing mask"]


def test_unknown_rule_rejected():
    with pytest.raises(ValueError):
        RuleEngine(active=("NO-Gloves",))


def test_empty_frame():
    r = RuleEngine().evaluate([])
    assert r.n_workers == 0 and r.compliance is None


def test_intersection_over_a():
    assert intersection_over_a((0, 0, 10, 10), (0, 0, 20, 20)) == 1.0
    assert intersection_over_a((0, 0, 10, 10), (5, 0, 20, 20)) == 0.5
    assert intersection_over_a((0, 0, 10, 10), (50, 50, 60, 60)) == 0.0
    assert intersection_over_a((0, 0, 0, 0), (0, 0, 1, 1)) == 0.0


def test_cooldown():
    t = [0.0]
    cd = Cooldown(10, clock=lambda: t[0])
    assert cd.allow("a")
    assert not cd.allow("a")
    assert cd.allow("b")             # independent keys
    t[0] = 9.9
    assert not cd.allow("a")
    t[0] = 10.0
    assert cd.allow("a")
