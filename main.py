#!/usr/bin/env python3

import argparse
import math
import random
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

RUNES = [
    "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ",
    "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛋ",
    "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛜ", "ᛟ", "ᛞ",
]

ORNAMENTS = [" ", " ", " ", "·", "•", "⋄", "◦", "˖", "˙", " "]

RUNE_EFFECTS = {
    "ᚠ": {"heat": 1.02, "flow": 0.42, "memory": 1.16, "phase": 0.18},
    "ᚢ": {"heat": 0.98, "flow": 0.48, "memory": 1.12, "phase": 0.30},
    "ᚦ": {"heat": 0.94, "flow": 0.36, "memory": 1.22, "phase": 0.54},
    "ᚨ": {"heat": 1.00, "flow": 0.40, "memory": 1.15, "phase": 0.22},
    "ᚱ": {"heat": 1.01, "flow": 0.50, "memory": 1.05, "phase": 0.38},
    "ᚲ": {"heat": 1.04, "flow": 0.39, "memory": 1.18, "phase": 0.60},
    "ᚷ": {"heat": 1.06, "flow": 0.44, "memory": 1.04, "phase": 0.48},
    "ᚹ": {"heat": 0.97, "flow": 0.54, "memory": 1.08, "phase": 0.28},
    "ᚺ": {"heat": 0.92, "flow": 0.34, "memory": 1.26, "phase": 0.68},
    "ᚾ": {"heat": 0.99, "flow": 0.46, "memory": 1.10, "phase": 0.26},
    "ᛁ": {"heat": 1.00, "flow": 0.38, "memory": 1.20, "phase": 0.12},
    "ᛃ": {"heat": 1.03, "flow": 0.47, "memory": 1.02, "phase": 0.42},
    "ᛇ": {"heat": 0.90, "flow": 0.35, "memory": 1.30, "phase": 0.78},
    "ᛈ": {"heat": 1.05, "flow": 0.43, "memory": 1.08, "phase": 0.34},
    "ᛉ": {"heat": 0.88, "flow": 0.33, "memory": 1.34, "phase": 0.86},
    "ᛋ": {"heat": 1.08, "flow": 0.52, "memory": 0.98, "phase": 0.20},
    "ᛏ": {"heat": 1.04, "flow": 0.37, "memory": 1.12, "phase": 0.50},
    "ᛒ": {"heat": 1.01, "flow": 0.40, "memory": 1.18, "phase": 0.58},
    "ᛖ": {"heat": 0.96, "flow": 0.37, "memory": 1.24, "phase": 0.72},
    "ᛗ": {"heat": 1.06, "flow": 0.41, "memory": 1.06, "phase": 0.24},
    "ᛚ": {"heat": 0.95, "flow": 0.45, "memory": 1.20, "phase": 0.64},
    "ᛜ": {"heat": 0.86, "flow": 0.31, "memory": 1.38, "phase": 0.94},
    "ᛟ": {"heat": 1.07, "flow": 0.36, "memory": 1.04, "phase": 0.56},
    "ᛞ": {"heat": 1.03, "flow": 0.46, "memory": 1.00, "phase": 0.32},
}


@dataclass
class Cell:
    energy: float = 0.0
    memory: float = 0.0
    flow_x: float = 0.0
    flow_y: float = 0.0
    phase: float = 0.0
    rune: str = " "
    age: int = 0


class RuneField:
    def __init__(
        self,
        width: int,
        height: int,
        seed_count: int,
        seed: int,
        cooling: float,
        diffusion: float,
        turbulence: float,
        birth_threshold: float,
        memory_decay: float,
        rune_decay: float,
        symmetry: float,
        ornament_bias: float,
    ) -> None:
        self.width = width
        self.height = height
        self.seed_count = seed_count
        self.seed = seed
        self.cooling = cooling
        self.diffusion = diffusion
        self.turbulence = turbulence
        self.birth_threshold = birth_threshold
        self.memory_decay = memory_decay
        self.rune_decay = rune_decay
        self.symmetry = max(0.0, min(1.0, symmetry))
        self.ornament_bias = max(0.0, min(1.0, ornament_bias))
        self.rng = random.Random(seed)
        self.grid: List[List[Cell]] = [[Cell() for _ in range(width)] for _ in range(height)]
        self.frame = 0
        self.seed_field()

    def mirrored_points(self, x: int, y: int) -> List[Tuple[int, int]]:
        pts = {
            (x, y),
            (self.width - 1 - x, y),
            (x, self.height - 1 - y),
            (self.width - 1 - x, self.height - 1 - y),
        }
        return list(pts)

    def seed_field(self) -> None:
        cx = (self.width - 1) / 2.0
        cy = (self.height - 1) / 2.0
        radius_x = self.width / 3.3
        radius_y = self.height / 3.6

        for _ in range(self.seed_count):
            angle = self.rng.uniform(0.0, math.tau)
            dist = math.sqrt(self.rng.random()) * 0.95
            x = int(cx + math.cos(angle) * radius_x * dist)
            y = int(cy + math.sin(angle) * radius_y * dist)
            x = max(0, min(self.width - 1, x))
            y = max(0, min(self.height - 1, y))

            rune = self.rng.choice(RUNES)
            effects = RUNE_EFFECTS[rune]
            points = self.mirrored_points(x, y) if self.rng.random() < self.symmetry else [(x, y)]

            for px, py in points:
                cell = self.grid[py][px]
                drift_angle = math.atan2(py - cy, px - cx + 1e-9)
                cell.energy = self.rng.uniform(0.36, 0.72) * effects["heat"]
                cell.memory = self.rng.uniform(0.42, 0.86) * effects["memory"]
                cell.flow_x = math.cos(drift_angle) * effects["flow"] * 0.35
                cell.flow_y = math.sin(drift_angle) * effects["flow"] * 0.35
                cell.phase = effects["phase"] + self.rng.random() * 0.12
                cell.rune = rune
                cell.age = self.rng.randint(0, 5)

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for dy in (-1, 0, 1):
            ny = y + dy
            if ny < 0 or ny >= self.height:
                continue
            for dx in (-1, 0, 1):
                nx = x + dx
                if nx < 0 or nx >= self.width:
                    continue
                if dx == 0 and dy == 0:
                    continue
                out.append((nx, ny))
        return out

    def dominant_rune(self, x: int, y: int) -> str:
        scores: Dict[str, float] = {}
        for nx, ny in self.neighbors(x, y):
            rune = self.grid[ny][nx].rune
            if rune == " ":
                continue
            score = self.grid[ny][nx].memory * 0.8 + self.grid[ny][nx].energy * 0.4
            scores[rune] = scores.get(rune, 0.0) + score
        if not scores:
            return self.rng.choice(RUNES)
        return max(scores.items(), key=lambda item: item[1])[0]

    def weighted_rune_shift(self, base_rune: str, energy: float, memory: float, phase: float) -> str:
        idx = RUNES.index(base_rune)
        shift = int(abs(math.sin(phase + energy * 0.35 + memory * 0.45)) * 2.2)
        direction = -1 if math.cos(phase + memory) < 0 else 1
        return RUNES[(idx + direction * shift) % len(RUNES)]

    def symmetry_blend(self, x: int, y: int, energy: float, memory: float, phase: float) -> Tuple[float, float, float]:
        mx = self.width - 1 - x
        my = self.height - 1 - y
        mirror = self.grid[my][mx]
        energy = energy * (1.0 - self.symmetry * 0.18) + mirror.energy * (self.symmetry * 0.18)
        memory = memory * (1.0 - self.symmetry * 0.22) + mirror.memory * (self.symmetry * 0.22)
        phase = phase * (1.0 - self.symmetry * 0.12) + mirror.phase * (self.symmetry * 0.12)
        return energy, memory, phase

    def step(self) -> None:
        new_grid: List[List[Cell]] = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.032)

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                nbs = self.neighbors(x, y)

                if nbs:
                    avg_energy = sum(self.grid[ny][nx].energy for nx, ny in nbs) / len(nbs)
                    avg_memory = sum(self.grid[ny][nx].memory for nx, ny in nbs) / len(nbs)
                    avg_flow_x = sum(self.grid[ny][nx].flow_x for nx, ny in nbs) / len(nbs)
                    avg_flow_y = sum(self.grid[ny][nx].flow_y for nx, ny in nbs) / len(nbs)
                    avg_phase = sum(self.grid[ny][nx].phase for nx, ny in nbs) / len(nbs)
                else:
                    avg_energy = cell.energy
                    avg_memory = cell.memory
                    avg_flow_x = cell.flow_x
                    avg_flow_y = cell.flow_y
                    avg_phase = cell.phase

                cx = (self.width - 1) / 2.0
                cy = (self.height - 1) / 2.0
                dx = x - cx
                dy = y - cy
                radial = math.hypot(dx, dy)
                radial_norm = radial / max(1.0, min(self.width, self.height) / 2.0)
                angle = math.atan2(dy, dx + 1e-9)

                curl_x = -math.sin(angle) * 0.08
                curl_y = math.cos(angle) * 0.08
                turbulence_x = self.rng.uniform(-self.turbulence, self.turbulence) * 0.35
                turbulence_y = self.rng.uniform(-self.turbulence, self.turbulence) * 0.35

                flow_x = cell.flow_x * 0.78 + avg_flow_x * 0.18 + curl_x + turbulence_x
                flow_y = cell.flow_y * 0.78 + avg_flow_y * 0.18 + curl_y + turbulence_y

                energy = (
                    cell.energy * (1.0 - self.cooling)
                    + avg_energy * self.diffusion
                    + pulse * 0.010
                    + max(0.0, 0.14 - radial_norm * 0.06)
                )
                memory = (
                    cell.memory * (1.0 - self.memory_decay)
                    + avg_memory * 0.16
                    + max(0.0, energy - 0.22) * 0.028
                )
                phase = (cell.phase * 0.86 + avg_phase * 0.14 + memory * 0.05 + energy * 0.04) % math.tau

                if cell.rune != " ":
                    effects = RUNE_EFFECTS[cell.rune]
                    energy *= effects["heat"] * 0.992
                    memory *= effects["memory"] * 0.994
                    flow_x *= effects["flow"] * 0.988
                    flow_y *= effects["flow"] * 0.988
                    phase = (phase + effects["phase"] * 0.014) % math.tau

                energy, memory, phase = self.symmetry_blend(x, y, energy, memory, phase)

                energy = max(0.0, min(1.6, energy))
                memory = max(0.0, min(1.8, memory))
                flow_x = max(-1.2, min(1.2, flow_x))
                flow_y = max(-1.2, min(1.2, flow_y))

                next_cell = new_grid[y][x]
                next_cell.energy = energy
                next_cell.memory = memory
                next_cell.flow_x = flow_x
                next_cell.flow_y = flow_y
                next_cell.phase = phase
                next_cell.age = cell.age + 1 if cell.rune != " " else 0

                pressure = energy * 0.72 + memory * 1.08 + abs(flow_x) * 0.04 + abs(flow_y) * 0.04

                if pressure >= self.birth_threshold:
                    base_rune = cell.rune if cell.rune != " " else self.dominant_rune(x, y)
                    if self.rng.random() < 0.78:
                        next_cell.rune = base_rune
                    else:
                        next_cell.rune = self.weighted_rune_shift(base_rune, energy, memory, phase)
                else:
                    if cell.rune != " " and pressure > self.birth_threshold * self.rune_decay:
                        next_cell.rune = cell.rune
                    else:
                        next_cell.rune = " "

        self.grid = new_grid
        self.inject_spores()
        self.frame += 1

    def inject_spores(self) -> None:
        count = max(1, (self.width * self.height) // 420)
        cx = (self.width - 1) / 2.0
        cy = (self.height - 1) / 2.0

        for _ in range(count):
            if self.rng.random() > 0.06:
                continue

            angle = self.rng.uniform(0.0, math.tau)
            radius_x = self.width / 3.8
            radius_y = self.height / 4.2
            dist = math.sqrt(self.rng.random()) * 0.85
            x = int(cx + math.cos(angle) * radius_x * dist)
            y = int(cy + math.sin(angle) * radius_y * dist)
            x = max(0, min(self.width - 1, x))
            y = max(0, min(self.height - 1, y))

            rune = self.dominant_rune(x, y)
            effects = RUNE_EFFECTS[rune]
            points = self.mirrored_points(x, y) if self.rng.random() < self.symmetry else [(x, y)]

            for px, py in points:
                cell = self.grid[py][px]
                if cell.energy < 0.20:
                    cell.energy += self.rng.uniform(0.06, 0.16) * effects["heat"]
                    cell.memory += self.rng.uniform(0.08, 0.18) * effects["memory"]
                    cell.phase = (cell.phase + effects["phase"] * 0.4) % math.tau
                    if cell.energy + cell.memory > self.birth_threshold * 0.82:
                        cell.rune = rune

    def ornament_char(self, cell: Cell) -> str:
        residue = cell.energy * 0.40 + cell.memory * 0.72
        if residue < 0.10:
            return " "
        if residue < 0.20:
            return self.rng.choice([" ", " ", "·"])
        if residue < 0.30:
            return self.rng.choice(["·", "˙", "◦"])
        if residue < 0.42:
            return self.rng.choice(["•", "⋄", "·"])
        return self.rng.choice(ORNAMENTS)

    def render(self) -> str:
        lines: List[str] = []
        for row in self.grid:
            chars: List[str] = []
            for cell in row:
                if cell.rune != " ":
                    intensity = cell.energy * 0.65 + cell.memory * 0.85
                    if intensity > 0.90:
                        chars.append(cell.rune)
                    elif intensity > 0.72:
                        chars.append(self.weighted_rune_shift(cell.rune, cell.energy, cell.memory, cell.phase))
                    else:
                        if self.rng.random() < self.ornament_bias:
                            chars.append(self.ornament_char(cell))
                        else:
                            chars.append(cell.rune)
                else:
                    chars.append(self.ornament_char(cell))
            lines.append("".join(chars))
        return "\n".join(lines)

    def stats(self) -> str:
        energies = []
        memories = []
        rune_count = 0
        unique = set()

        for row in self.grid:
            for cell in row:
                energies.append(cell.energy)
                memories.append(cell.memory)
                if cell.rune != " ":
                    rune_count += 1
                    unique.add(cell.rune)

        mean_energy = sum(energies) / len(energies) if energies else 0.0
        mean_memory = sum(memories) / len(memories) if memories else 0.0

        return (
            f"frame={self.frame} "
            f"runes={rune_count} "
            f"unique={len(unique)} "
            f"energy={mean_energy:.3f} "
            f"memory={mean_memory:.3f}"
        )


def detect_size(width: int, height: int) -> Tuple[int, int]:
    if width > 0 and height > 0:
        return width, height
    size = shutil.get_terminal_size((100, 32))
    final_width = width if width > 0 else max(20, size.columns)
    final_height = height if height > 0 else max(10, size.lines - 2)
    return final_width, final_height


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="runefield")
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=14)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.09)
    parser.add_argument("--cooling", type=float, default=0.075)
    parser.add_argument("--diffusion", type=float, default=0.10)
    parser.add_argument("--turbulence", type=float, default=0.07)
    parser.add_argument("--birth-threshold", type=float, default=0.78)
    parser.add_argument("--memory-decay", type=float, default=0.018)
    parser.add_argument("--rune-decay", type=float, default=0.84)
    parser.add_argument("--symmetry", type=float, default=0.90)
    parser.add_argument("--ornament-bias", type=float, default=0.55)
    parser.add_argument("--stats", action="store_true")
    return parser.parse_args()


def clear_and_home() -> None:
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def main() -> int:
    args = parse_args()
    width, height = detect_size(args.width, args.height)

    field = RuneField(
        width=width,
        height=height,
        seed_count=args.seed_count,
        seed=args.seed,
        cooling=args.cooling,
        diffusion=args.diffusion,
        turbulence=args.turbulence,
        birth_threshold=args.birth_threshold,
        memory_decay=args.memory_decay,
        rune_decay=args.rune_decay,
        symmetry=args.symmetry,
        ornament_bias=args.ornament_bias,
    )

    frame_limit = args.frames if args.frames > 0 else None
    frame = 0

    try:
        while True:
            clear_and_home()
            sys.stdout.write(field.render())
            sys.stdout.write("\n")
            if args.stats:
                sys.stdout.write(field.stats())
                sys.stdout.write("\n")
            sys.stdout.flush()

            field.step()
            frame += 1

            if frame_limit is not None and frame >= frame_limit:
                break

            time.sleep(args.delay)
    except KeyboardInterrupt:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
