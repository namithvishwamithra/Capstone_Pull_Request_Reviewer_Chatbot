import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: set[int] = field(default_factory=set)
    deleted_line_count: int = 0


@dataclass
class DiffFile:
    path: str
    added_lines: set[int] = field(default_factory=set)
    changed_line_count: int = 0
    is_binary: bool = False
    is_generated: bool = False
    hunks: list[DiffHunk] = field(default_factory=list)


def _is_skipped(path: str) -> bool:
    lower = path.lower()
    name = PurePosixPath(lower).name
    return (
        name.endswith((".lock", ".min.js", ".min.css", ".map"))
        or name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}
        or any(
            part in {"generated", "vendor", "node_modules", "dist", "build"}
            for part in lower.split("/")
        )
        or "generated" in name
    )


def parse_unified_diff(diff: str) -> list[DiffFile]:
    """Parse file paths, changed-line counts, and added line numbers from a unified diff."""
    files: list[DiffFile] = []
    current: DiffFile | None = None
    current_hunk: DiffHunk | None = None
    new_line = 0
    in_hunk = False
    old_path: str | None = None
    hunk_header = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current = None
            current_hunk = None
            old_path = None
            in_hunk = False
            continue
        if line.startswith("--- "):
            raw_old_path = line[4:].strip()
            old_path = raw_old_path[2:] if raw_old_path.startswith("a/") else raw_old_path
            continue
        if line.startswith("+++ "):
            raw_path = line[4:].strip()
            path = raw_path[2:] if raw_path.startswith("b/") else raw_path
            if path == "/dev/null":
                if old_path and old_path != "/dev/null":
                    current = DiffFile(path=old_path, is_generated=_is_skipped(old_path))
                    files.append(current)
                else:
                    current = None
                current_hunk = None
                continue
            current = DiffFile(path=path, is_generated=_is_skipped(path))
            files.append(current)
            current_hunk = None
            continue
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            if current:
                current.is_binary = True
            in_hunk = False
            current_hunk = None
            continue
        header = hunk_header.match(line)
        if header:
            old_start = int(header.group(1))
            old_count = int(header.group(2) or 1)
            new_start = int(header.group(3))
            new_count = int(header.group(4) or 1)
            new_line = new_start
            in_hunk = True
            if current is not None:
                current_hunk = DiffHunk(old_start, old_count, new_start, new_count)
                current.hunks.append(current_hunk)
            continue
        if not in_hunk or current is None or current_hunk is None or line.startswith("\\"):
            continue
        if line.startswith("+"):
            current.added_lines.add(new_line)
            current_hunk.added_lines.add(new_line)
            current.changed_line_count += 1
            new_line += 1
        elif line.startswith("-"):
            current.changed_line_count += 1
            current_hunk.deleted_line_count += 1
        elif line.startswith(" "):
            new_line += 1
    return files


def changed_line_count(files: list[DiffFile]) -> int:
    return sum(file.changed_line_count for file in files)


def supported_files(files: list[DiffFile]) -> tuple[list[DiffFile], list[str]]:
    eligible = [file for file in files if not file.is_binary and not file.is_generated]
    excluded = [file.path for file in files if file.is_binary or file.is_generated]
    return eligible, excluded


def validate_finding_location(path: str, start: int, end: int, files: list[DiffFile]) -> bool:
    file = next(
        (
            item
            for item in files
            if item.path == path and not item.is_binary and not item.is_generated
        ),
        None,
    )
    return bool(
        file and start <= end and all(line in file.added_lines for line in range(start, end))
    )
