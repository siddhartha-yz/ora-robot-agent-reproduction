"""Exact random proposal generator from the three archived ORA controls."""
from __future__ import annotations

import random

SEEDS = (20261107, 20261108, 20261109)
BOUNDS = ((-.6, .6), (-.5, .5), (-.1, 1.3))
MARGIN = .05


def actions(seed: int, initial_position: list[float]) -> list[dict]:
    rng = random.Random(seed)
    waypoint = list(initial_position)
    result = []
    for _ in range(200):
        category = rng.random()
        if category < .65:
            waypoint = [round(max(lo + MARGIN, min(hi - MARGIN, p + rng.uniform(-.04, .04))), 6)
                        for p, (lo, hi) in zip(waypoint, BOUNDS)]
            result.append({
                'tool': 'move_pose', 'position_mode': 'absolute',
                'position_m': list(waypoint), 'orientation_mode': 'hold_current',
                'interaction': rng.choice(('free_space', 'precision', 'contact_approach')),
            })
        elif category < .80:
            result.append({
                'tool': 'move_pose', 'position_mode': 'absolute', 'position_m': list(waypoint),
                'orientation_mode': 'axis_angle_delta',
                'rotation_axis': rng.choice(('x', 'y', 'z')),
                'rotation_angle_deg': round(rng.uniform(-30, 30), 6),
                'orientation_frame': 'world', 'interaction': 'precision',
            })
        else:
            result.append({'tool': 'set_gripper', 'action': rng.choice(('open', 'close'))})
    return result
