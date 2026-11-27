"""Pure scoring for the self-check mode. No network, no logging, no storage.

Thresholds are read from self_scoring.json (DRAFT, not verified against primary sources).
"""
import json
import os

_SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "self_scoring.json")


class ScoreError(ValueError):
    """Invalid input. The message never contains the submitted values."""


def load_spec(path=_SPEC_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SPEC = load_spec()


def _check_answers(answers, n_items, allowed):
    if not isinstance(answers, list):
        raise ScoreError("answers must be a list")
    if len(answers) != n_items:
        raise ScoreError("wrong number of answers")
    for v in answers:
        if isinstance(v, bool) or not isinstance(v, int) or v not in allowed:
            raise ScoreError("answer value out of range")


def _zone(zones, total):
    for z in zones:
        if total <= z["max"]:
            return z["key"]
    raise ScoreError("total outside zone table")


def _check_sex(sex):
    if sex not in SPEC["_meta"]["sex_values"]:
        raise ScoreError("sex must be M or F")


def _score_simple(test, t, answers, sex):
    _check_answers(answers, t["items"], t["allowed"])
    mode = t["mode"]
    out = {"test": test, "mode": mode, "max_total": t["max_total"]}
    if mode == "score_with_caveat":
        a = answers
        if t.get("reverse_item_indices"):
            top = max(t["allowed"])
            rev = set(t["reverse_item_indices"])
            a = [top - v if i in rev else v for i, v in enumerate(answers)]
        out["total"] = sum(a)
        out["zone"] = None
    elif mode == "zones":
        total = sum(answers) * t.get("multiplier", 1)
        out["total"] = total
        out["zone"] = _zone(t["zones"], total)
    elif mode == "cutoff_by_sex":
        if t.get("requires_sex"):
            _check_sex(sex)
        total = sum(answers)
        cut = t["cutoff_by_sex"][sex]
        out["total"] = total
        out["cutoff"] = cut
        out["cutoff_met"] = total >= cut
        out["zone"] = "positive" if total >= cut else "negative"
    else:
        raise ScoreError("unsupported mode")
    if "crisis_item_index" in t:
        out["crisis"] = answers[t["crisis_item_index"]] > t["crisis_if_gt"]
    else:
        out["crisis"] = False
    return out


def score(test, answers, sex=None):
    """Return a result dict or raise ScoreError."""
    if not isinstance(test, str):
        raise ScoreError("test must be a string")
    if test in SPEC["excluded"]:
        raise ScoreError("test is not available in self mode")
    t = SPEC["tests"].get(test)
    if t is None:
        raise ScoreError("unknown test")
    if t["mode"] != "composite":
        return _score_simple(test, t, answers, sex)

    # composite (express): each part is scored separately, there is no overall total
    _check_answers(answers, t["items"], t["allowed"])
    if t.get("requires_sex"):
        _check_sex(sex)
    parts = {}
    for p in t["parts"]:
        sub = answers[p["start"]:p["end"]]
        if any(v not in p["allowed"] for v in sub):
            raise ScoreError("answer value out of range")
        parts[p["test"]] = _score_simple(p["test"], SPEC["tests"][p["test"]], sub, sex)
    return {
        "test": test,
        "mode": "composite",
        "parts": parts,
        "crisis": answers[t["crisis_item_index"]] > t["crisis_if_gt"],
    }
