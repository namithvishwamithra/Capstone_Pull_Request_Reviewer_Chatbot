import re

MAX_CHUNK_CHARS = 18_000
_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def _line_counts(lines: list[str]) -> tuple[int, int]:
    old_count = 0
    new_count = 0
    for line in lines:
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            new_count += 1
        elif line.startswith("-"):
            old_count += 1
        elif line.startswith(" "):
            old_count += 1
            new_count += 1
    return old_count, new_count


def _render_hunk(
    old_start: int,
    new_start: int,
    body: list[str],
    heading: str,
) -> list[str]:
    old_count, new_count = _line_counts(body)
    header = f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{heading}"
    return [header, *body]


def _split_file(section: list[str], max_chars: int) -> list[str]:
    first_hunk = next(
        (index for index, line in enumerate(section) if _HUNK_HEADER.match(line)),
        None,
    )
    if first_hunk is None:
        return ["\n".join(section)]

    prefix = section[:first_hunk]
    chunks: list[str] = []
    hunk_header = ""
    hunk_body: list[str] = []

    def flush_hunk() -> None:
        nonlocal hunk_body
        if not hunk_body:
            return
        match = _HUNK_HEADER.match(hunk_header)
        if match is None:
            hunk_body = []
            return
        old_start = int(match.group(1))
        new_start = int(match.group(3))
        heading = match.group(5)
        consumed_old = 0
        consumed_new = 0
        body_chunk: list[str] = []
        current_size = sum(len(line) + 1 for line in prefix) + len(hunk_header)

        def flush_body_chunk() -> None:
            nonlocal body_chunk, consumed_old, consumed_new, current_size
            if not body_chunk:
                return
            rendered = _render_hunk(
                old_start + consumed_old,
                new_start + consumed_new,
                body_chunk,
                heading,
            )
            chunks.append("\n".join([*prefix, *rendered]))
            old_count, new_count = _line_counts(body_chunk)
            consumed_old += old_count
            consumed_new += new_count
            body_chunk = []
            current_size = sum(len(line) + 1 for line in prefix) + len(hunk_header)

        for line in hunk_body:
            if body_chunk and current_size + len(line) + 1 > max_chars:
                flush_body_chunk()
            body_chunk.append(line)
            current_size += len(line) + 1
        flush_body_chunk()
        hunk_body = []

    for line in section[first_hunk:]:
        if _HUNK_HEADER.match(line):
            flush_hunk()
            hunk_header = line
            hunk_body = []
        else:
            hunk_body.append(line)
    flush_hunk()
    return chunks


def chunk_diff(diff: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split unified diffs by file and hunk, preserving absolute changed-line coordinates."""
    sections: list[list[str]] = []
    current: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git ") and current:
            sections.append(current)
            current = []
        current.append(line)
    if current:
        sections.append(current)

    chunks: list[str] = []
    for section in sections:
        if len("\n".join(section)) <= max_chars:
            chunks.append("\n".join(section))
        else:
            chunks.extend(_split_file(section, max_chars))
    return chunks
