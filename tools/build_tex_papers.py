#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = REPO_ROOT / "paper"

PAPERS = {
    "deriving_the_particle_zoo_from_observer_consistency": (
        PAPER_DIR / "deriving_the_particle_zoo_from_observer_consistency.tex"
    ),
    "observers_are_all_you_need": PAPER_DIR / "observers_are_all_you_need.tex",
    "reality_as_consensus_protocol": PAPER_DIR / "reality_as_consensus_protocol.tex",
    "recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact": (
        PAPER_DIR / "recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact.tex"
    ),
    "screen_microphysics_and_observer_synchronization": PAPER_DIR / "screen_microphysics_and_observer_synchronization.tex",
}

RELEASE_TRACKED = (
    "recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact",
    "observers_are_all_you_need",
    "reality_as_consensus_protocol",
    "screen_microphysics_and_observer_synchronization",
    "deriving_the_particle_zoo_from_observer_consistency",
)
RELEASE_TRACKED_SET = set(RELEASE_TRACKED)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the hand-authored TeX papers in paper/ with tectonic.",
    )
    parser.add_argument(
        "papers",
        nargs="*",
        help="Optional paper ids to build. Defaults to all known papers.",
    )
    parser.add_argument(
        "--release-only",
        action="store_true",
        help="Build only the release-tracked paper bundle used by paper_release_manifest.json.",
    )
    parser.add_argument(
        "--supplemental-only",
        action="store_true",
        help="Build only supplemental papers that are not yet release-tracked.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the known paper ids and exit.",
    )
    return parser.parse_args()


def resolve_targets(args: argparse.Namespace) -> list[str]:
    if args.release_only and args.supplemental_only:
        raise SystemExit("choose at most one of --release-only or --supplemental-only")

    if args.list:
        for paper_id in sorted(PAPERS):
            marker = "release" if paper_id in RELEASE_TRACKED_SET else "supplemental"
            print(f"{paper_id}\t{marker}")
        raise SystemExit(0)

    if args.papers:
        unknown = [paper_id for paper_id in args.papers if paper_id not in PAPERS]
        if unknown:
            raise SystemExit(f"unknown paper ids: {', '.join(sorted(unknown))}")
        return args.papers

    if args.release_only:
        return list(RELEASE_TRACKED)
    if args.supplemental_only:
        return sorted(set(PAPERS) - RELEASE_TRACKED_SET)
    return sorted(PAPERS)


def build_one(paper_id: str) -> None:
    tex_path = PAPERS[paper_id]
    if not tex_path.exists():
        raise SystemExit(f"missing TeX source: {tex_path}")

    cmd = ["tectonic", "-X", "compile", tex_path.name]
    result = subprocess.run(cmd, cwd=PAPER_DIR, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout[-8000:])
        if result.stderr.strip():
            print(result.stderr[-8000:])
        raise SystemExit(f"tectonic failed for {paper_id}")

    print(PAPER_DIR / f"{tex_path.stem}.pdf")


def main() -> int:
    if shutil.which("tectonic") is None:
        raise SystemExit("tectonic is required but was not found in PATH")

    args = parse_args()
    for paper_id in resolve_targets(args):
        build_one(paper_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
