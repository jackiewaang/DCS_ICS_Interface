import json
import sys
import time
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: test_job.py <remote_dir> <embedding|llm>")

    remote_dir = Path(sys.argv[1])
    job_type = sys.argv[2]
    if job_type not in {"embedding", "llm"}:
        raise SystemExit(f"Unsupported job type: {job_type}")

    input_path = remote_dir / "input.json"
    output_path = remote_dir / "output.json"
    temporary_output_path = remote_dir / "output.json.tmp"

    with input_path.open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if not isinstance(payload, dict):
        raise ValueError("input.json must contain a JSON object.")

    time.sleep(5)

    result = {
        "status": "success",
        "job_type": job_type,
        "received_payload": payload,
        "message": "Job completed successfully.",
    }

    with temporary_output_path.open("w", encoding="utf-8") as output_file:
        json.dump(result, output_file)

    temporary_output_path.replace(output_path)


if __name__ == "__main__":
    main()
