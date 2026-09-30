from app.services.diff_parser import (
    changed_line_count,
    parse_unified_diff,
    supported_files,
    validate_finding_location,
)

DIFF = """diff --git a/src/auth.py b/src/auth.py
index 111..222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -4,2 +4,3 @@
 existing()
+dangerous()
-old()
+replacement()
\\ No newline at end of file
diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1 +1 @@
-old
+new
"""


def test_parser_tracks_added_lines_and_changed_count():
    files = parse_unified_diff(DIFF)
    assert [file.path for file in files] == ["src/auth.py", "package-lock.json"]
    assert files[0].added_lines == {5, 6}
    assert len(files[0].hunks) == 1
    assert files[0].hunks[0].old_start == 4
    assert files[0].hunks[0].new_start == 4
    assert files[0].hunks[0].added_lines == {5, 6}
    assert files[0].hunks[0].deleted_line_count == 1
    assert changed_line_count(files) == 5


def test_excludes_lockfiles_by_default_and_validates_changed_ranges():
    files = parse_unified_diff(DIFF)
    eligible, excluded = supported_files(files)
    assert [file.path for file in eligible] == ["src/auth.py"]
    assert excluded == ["package-lock.json"]
    assert validate_finding_location("src/auth.py", 5, 6, files)
    assert not validate_finding_location("src/auth.py", 4, 5, files)
    assert not validate_finding_location("package-lock.json", 1, 1, files)


def test_finding_range_rejects_unmodified_end_line():
    files = parse_unified_diff(DIFF)
    assert not validate_finding_location("src/auth.py", 6, 7, files)


def test_parser_accepts_deleted_file_without_claiming_added_code():
    deleted = """diff --git a/old.txt b/old.txt
--- a/old.txt
+++ /dev/null
@@ -1 +0,0 @@
-removed line
"""
    files = parse_unified_diff(deleted)
    assert files[0].path == "old.txt"
    assert files[0].added_lines == set()
    assert changed_line_count(files) == 1
