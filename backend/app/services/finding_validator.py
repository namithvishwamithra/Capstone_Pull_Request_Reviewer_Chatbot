from collections.abc import Collection

from app.schemas.review import Finding
from app.services.diff_parser import DiffFile, validate_finding_location


def validate_findings(
    candidates: list[Finding], eligible_paths: Collection[str], files: list[DiffFile]
) -> list[Finding]:
    """Keep only model findings grounded in an eligible file's added diff lines."""
    return [
        finding
        for finding in candidates
        if finding.file in eligible_paths
        and validate_finding_location(
            finding.file,
            finding.line_start,
            finding.line_end,
            files,
        )
    ]
