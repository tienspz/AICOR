from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.sync_vibe_skills import SyncError, sync_skills


def _write_skill(root: Path, name: str, body: str = "Skill instructions.\n") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use this skill for a focused task.\n---\n\n{body}",
        encoding="utf-8",
    )
    return skill


def test_sync_copies_skill_and_is_idempotent():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = root / "source"
        destination = root / "destination"
        skill = _write_skill(source, "example-skill")
        (skill / "LICENSE").write_text("license text\n", encoding="utf-8")

        first = sync_skills(source, destination)
        second = sync_skills(source, destination)

        assert first.installed == ("example-skill",)
        assert first.unchanged == ()
        assert second.installed == ()
        assert second.unchanged == ("example-skill",)
        assert (destination / "example-skill" / "LICENSE").read_text(encoding="utf-8") == "license text\n"


def test_check_only_reports_missing_without_creating_destination():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = root / "source"
        destination = root / "not-created"
        _write_skill(source, "example-skill")

        result = sync_skills(source, destination, check_only=True)

        assert result.missing == ("example-skill",)
        assert not destination.exists()


def test_sync_refuses_to_overwrite_and_does_not_partially_copy():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = root / "source"
        destination = root / "destination"
        _write_skill(source, "a-conflicting-skill")
        _write_skill(source, "another-skill")
        _write_skill(destination, "a-conflicting-skill", body="Different local instructions.\n")

        with pytest.raises(SyncError, match="Refusing to overwrite"):
            sync_skills(source, destination)

        assert not (destination / "another-skill").exists()
        assert "Different local instructions." in (
            destination / "a-conflicting-skill" / "SKILL.md"
        ).read_text(encoding="utf-8")


def test_sync_rejects_skill_name_that_does_not_match_folder():
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = root / "source"
        skill = _write_skill(source, "folder-name")
        (skill / "SKILL.md").write_text(
            "---\nname: different-name\ndescription: Invalid name.\n---\n",
            encoding="utf-8",
        )

        with pytest.raises(SyncError, match="must match its folder"):
            sync_skills(source, root / "destination")
