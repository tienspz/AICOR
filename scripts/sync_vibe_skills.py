"""Install the tracked Vibe Code skills into a compatible host directory."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "vibe-code" / "skills"
DEFAULT_DESTINATION = REPOSITORY_ROOT / ".agents" / "skills"
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SyncError(Exception):
    """Raised when a skill cannot be validated or installed safely."""


@dataclass(frozen=True)
class SyncResult:
    installed: tuple[str, ...]
    unchanged: tuple[str, ...]
    missing: tuple[str, ...] = ()


def _frontmatter_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", frontmatter, re.MULTILINE)
    if match is None:
        return None
    return match.group(1).strip().strip("\"'")


def discover_skills(source_root: Path) -> tuple[Path, ...]:
    if not source_root.is_dir():
        raise SyncError(f"Skill source directory does not exist: {source_root}")

    skills = tuple(
        sorted(
            (path for path in source_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()),
            key=lambda path: path.name,
        )
    )
    if not skills:
        raise SyncError(f"No skill folders containing SKILL.md were found in: {source_root}")

    for skill in skills:
        if not SKILL_NAME_PATTERN.fullmatch(skill.name):
            raise SyncError(f"Skill folder name is not portable: {skill.name}")
        _validate_skill(skill)
        for path in skill.rglob("*"):
            if path.is_symlink():
                raise SyncError(f"Symlinks are not supported in skill bundles: {path}")
    return skills


def _validate_skill(skill: Path) -> None:
    content = (skill / "SKILL.md").read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SyncError(f"Missing YAML frontmatter in {skill / 'SKILL.md'}")

    try:
        closing_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as error:
        raise SyncError(f"Unclosed YAML frontmatter in {skill / 'SKILL.md'}") from error

    frontmatter = "\n".join(lines[1:closing_index])
    name = _frontmatter_value(frontmatter, "name")
    description = _frontmatter_value(frontmatter, "description")
    if name != skill.name:
        raise SyncError(f"Skill name in {skill / 'SKILL.md'} must match its folder ({skill.name!r})")
    if not description or len(description) > 1024:
        raise SyncError(f"Skill description in {skill / 'SKILL.md'} must contain 1-1024 characters")


def _file_map(directory: Path) -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise SyncError(f"Symlinks are not supported in skill bundles: {path}")
        if path.is_file():
            files[path.relative_to(directory)] = path.read_bytes()
    return files


def _same_tree(source: Path, destination: Path) -> bool:
    if not destination.is_dir():
        return False
    return _file_map(source) == _file_map(destination)


def sync_skills(
    source_root: Path,
    destination_root: Path,
    *,
    check_only: bool = False,
) -> SyncResult:
    skills = discover_skills(source_root)
    conflicts = [
        skill.name
        for skill in skills
        if (destination_root / skill.name).exists()
        and not _same_tree(skill, destination_root / skill.name)
    ]
    if conflicts:
        names = ", ".join(conflicts)
        raise SyncError(
            f"Refusing to overwrite skill(s) with different contents: {names}. "
            "Resolve the conflict manually, then re-run the sync."
        )

    unchanged = tuple(
        skill.name
        for skill in skills
        if _same_tree(skill, destination_root / skill.name)
    )
    missing = tuple(skill.name for skill in skills if skill.name not in unchanged)
    if check_only or not missing:
        return SyncResult(installed=(), unchanged=unchanged, missing=missing)

    destination_root.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        if skill.name in missing:
            shutil.copytree(skill, destination_root / skill.name)
    return SyncResult(installed=missing, unchanged=unchanged)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help="Target skills directory (default: .agents/skills in the repository)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the destination matches the canonical skills without writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    destination = args.destination
    if not destination.is_absolute():
        destination = REPOSITORY_ROOT / destination

    try:
        result = sync_skills(SOURCE_ROOT, destination, check_only=args.check)
    except (OSError, SyncError) as error:
        print(f"Skill sync failed: {error}", file=sys.stderr)
        return 1

    if result.missing:
        print(f"Skills not synchronized in {destination}: {', '.join(result.missing)}", file=sys.stderr)
        return 1
    if result.installed:
        print(f"Installed in {destination}: {', '.join(result.installed)}")
    else:
        print(f"Skills are synchronized in {destination}: {', '.join(result.unchanged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
