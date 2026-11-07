"""Check the published data and reproduce the recorded random proposals offline."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from random_actions import BOUNDS, MARGIN, SEEDS, actions

ROOT = Path(__file__).resolve().parents[1] / "evidence"


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    result = read("deepseek/result.json")
    evaluation = read("deepseek/evaluation.json")
    trace = read("deepseek/tool-to-action-trace.json")
    transcript = read("deepseek/visible-turns.json")
    cost = read("deepseek/cost.json")
    check(result["official_success"] is True and result["behavioral_sample_valid"] is True
          and evaluation["status"] == "valid" and evaluation["official_success"] is True
          and result["run_id"] == evaluation["run_id"] == transcript["run_id"],
          "DeepSeek run and evaluation disagree")
    check(result["decisions"] == len(trace["world_actions"]) == 7
          and result["model_calls"] == len(transcript["rounds"]) == len(trace["calls"]) == 16,
          "DeepSeek recorded counts disagree")
    motions = trace["world_actions"]
    terminal = trace["termination_evidence"]["first_termination"]
    check(sum(m["steps_used"] for m in motions) == terminal["sim_step"] == 498
          and terminal["action_id"] == motions[-1]["action_id"]
          and [m["terminal_after_action"] for m in motions] == [False] * 6 + [True],
          "DeepSeek terminal motion does not match the official boundary")
    for observed, recorded in zip(transcript["rounds"], trace["calls"]):
        check(observed["model_call_id"] == recorded["response"]["model_call_id"]
              and observed["visible_content"] == recorded["visible_content"]["content"],
              f"Visible response mismatch at round {observed['round']}")
    check(abs(cost["total_estimated_cny"] -
              (cost["episode"]["estimated_cny"] + cost["preflight"]["estimated_cny"])) < 1e-8,
          "Cost summary does not match the two billed-use categories")

    protocol = read("random/protocol.json")
    analysis = read("random/analysis.json")
    check(protocol["rng_seeds"] == list(SEEDS), "Unexpected random control seeds")
    totals: Counter = Counter()
    for seed, observed_steps, audited in zip(SEEDS, (1372, 1499, 1437), analysis["runs"]):
        result = read(f"random/{seed}/result.json")
        evaluation = read(f"random/{seed}/evaluation.json")
        spec = read(f"random/{seed}/recorded-spec.json")
        seq = actions(seed, protocol["initial_public_tcp_m"])
        check(spec["seed"] == protocol["environment_seed"] == 0
              and spec["policy"]["kind"] == "scripted"
              and seq == spec["policy"]["actions"] and len(seq) == 200,
              f"Recorded random policy mismatch: {seed}")
        counts = Counter()
        for action in seq:
            if action["tool"] == "set_gripper":
                counts["gripper_" + action["action"]] += 1
            else:
                counts["rotation" if action["orientation_mode"] == "axis_angle_delta" else "translation"] += 1
                check(all(lo + MARGIN <= p <= hi - MARGIN
                          for p, (lo, hi) in zip(action["position_m"], BOUNDS)),
                      f"Out-of-bounds planned waypoint: {seed}")
        check(counts == protocol["counts"][str(seed)], f"Distribution count mismatch: {seed}")
        check(audited["rng_seed"] == seed and audited["run_id"] == result["run_id"] == evaluation["run_id"]
              and result["official_success"] is False and result["behavioral_sample_valid"] is True
              and result["termination"] == "robot_decision_budget" and result["model_calls"] == 0
              and result["decisions"] == spec["budgets"]["max_robot_decisions"] == 80
              and evaluation["status"] == "valid" and evaluation["official_success"] is False
              and audited["trace"]["final_receipt_sim_steps_total"] == observed_steps,
              f"Random evaluation or receipt mismatch: {seed}")
        totals["tool_proposals"] += audited["trace"]["tool_proposals"]
        totals["consumed_decisions"] += result["decisions"]
        totals["nonconsumed_receipts"] += result["refused_proposals"]
    check(len(analysis["runs"]) == len(SEEDS)
          and all(analysis["aggregate"][k] == v for k, v in totals.items()),
          "Random run totals disagree with the audit")
    print("PASS: DeepSeek 1/1, random 0/3; 16 turns, 7 actions, 600 random proposals verified.")


if __name__ == "__main__":
    main()
