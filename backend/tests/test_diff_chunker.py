from app.services.diff_chunker import chunk_diff
from app.services.diff_parser import parse_unified_diff


def test_large_hunk_chunks_keep_absolute_added_line_numbers():
    patch = (
        "diff --git a/src/example.py b/src/example.py\n"
        "index abc..def 100644\n"
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -39,0 +40,12 @@ function\n"
        + "".join(f"+value_{index:02d} = {index}\n" for index in range(12))
    )
    chunks = chunk_diff(patch, max_chars=150)
    assert len(chunks) > 1
    parsed = [parse_unified_diff(chunk)[0] for chunk in chunks]
    assert [line for file in parsed for line in sorted(file.added_lines)] == list(range(40, 52))
    assert all("src/example.py" in chunk for chunk in chunks)
