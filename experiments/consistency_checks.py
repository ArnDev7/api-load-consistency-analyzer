import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional
import pandas as pd
from app.database import get_session_factory
from app.services.consistency_service import verify_database_consistency
from app.observability.logging import logger



def run_consistency_audit(
    output_dir: Optional[Path] = None,
    tag: str = "latest",
) -> dict:
    """Execute consistency verification and optionally export JSON and CSV artifacts."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        report = verify_database_consistency(db)
        report_dict = report.model_dump()

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # JSON export
            json_file = output_dir / f"consistency_{tag}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2)

            # CSV export of per-item details
            if report_dict.get("details"):
                csv_file = output_dir / f"consistency_{tag}.csv"
                df = pd.DataFrame(report_dict["details"])
                df.to_csv(csv_file, index=False)

        status_str = "PASSED" if report.consistent else "FAILED"
        logger.info(
            "Consistency Audit [%s]: %s (Items: %d, Active Res: %d, Violations: %d)",
            tag,
            status_str,
            report.total_items,
            report.active_reservations,
            report.violations_count,
        )
        return report_dict
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run database consistency audit")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to export results")
    parser.add_argument("--tag", type=str, default="manual_check", help="Tag for exported filenames")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else None
    res = run_consistency_audit(output_dir=out_dir, tag=args.tag)
    print(json.dumps(res, indent=2))
