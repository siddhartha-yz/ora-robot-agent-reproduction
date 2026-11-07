"""Create new ORA RunSpecs for the recorded random control; do not launch them."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from random_actions import SEEDS, actions

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "random"


def main() -> None:
    from ora.agent.model_services.operator import binding

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", required=True, type=Path, help="Fresh ORA service readiness report")
    parser.add_argument("--dest", required=True, type=Path, help="New directory for generated specs")
    parser.add_argument("--experiment", required=True, help="Unused experiment name in your ORA outputs")
    parser.add_argument("--host", default="single-gpu", help="Registered ORA execution host")
    parser.add_argument("--resource-profile", default="libero-gpu0")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,59}", args.experiment):
        parser.error("--experiment must be a safe name of at most 60 characters")

    initial = json.loads((EVIDENCE / "protocol.json").read_text())["initial_public_tcp_m"]
    generated = {}
    for seed in SEEDS:
        spec = json.loads((EVIDENCE / str(seed) / "recorded-spec.json").read_text())
        seq = actions(seed, initial)
        if seq != spec["policy"]["actions"]:
            raise ValueError(f"Generated actions differ from the archived sequence for {seed}")
        spec["policy"]["actions"] = seq
        spec["prerequisite"] = binding(
            args.readiness, spec["policy"]["tool_surface"]["profile"],
            spec["prerequisite"]["capability_scope"],
        )
        spec.update(experiment=args.experiment, output_workspace=f"outputs/{args.experiment}")
        spec["runtime"].update(required_host=args.host, resource_profile=args.resource_profile)
        spec["launch_admission"]["cohort_id"] = args.experiment
        generated[seed] = spec

    args.dest.mkdir(parents=True, exist_ok=False)
    for seed, spec in generated.items():
        path = args.dest / f"random-{seed}.json"
        path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
