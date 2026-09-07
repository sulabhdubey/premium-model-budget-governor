"""Stage public task inputs separately from grading criteria. No host/model calls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "examples" / "field-trial"


def prepare(task_id, output, *, source=SOURCE):
    source = source.resolve(strict=True)
    suite_bytes = (source / "suite.json").read_bytes()
    suite = json.loads(suite_bytes)
    snapshot = json.loads((source / "snapshot.json").read_bytes())
    if snapshot["suite_id"] != suite["id"] or sha256(suite_bytes).hexdigest() != snapshot["files"]["suite.json"]:
        raise ValueError("suite snapshot changed; review and preregister a new version")
    matches = [task for task in suite["tasks"] if task["id"] == task_id]
    if len(matches) != 1:
        raise ValueError("select an existing task ID")
    task = matches[0]
    inputs = {}
    for name in task["inputs"]:
        if Path(name).name != name or name in {"suite.json", "snapshot.json", "task.txt"}:
            raise ValueError("only named task input files may be staged")
        path = (source / name).resolve(strict=True)
        if not path.is_relative_to(source):
            raise ValueError("task input escaped the fixture directory")
        data = path.read_bytes()
        if sha256(data).hexdigest() != snapshot["files"][name]:
            raise ValueError("task input changed; review and preregister a new version")
        inputs[name] = data
    output = Path(output)
    # Refuse replacement even for an empty directory or a dangling symlink.
    output.mkdir(parents=False, exist_ok=False)
    for name, data in inputs.items():
        (output / name).write_bytes(data)
    (output / "task.txt").write_text(task["prompt"] + "\n", encoding="utf-8")
    return {"task_id": task_id, "suite_id": suite["id"], "input_files": sorted(inputs),
            "suite_sha256": snapshot["files"]["suite.json"], "model_calls_started": 0,
            "grading_criteria_included": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.task, args.output), indent=2))
    except (OSError, ValueError, KeyError):
        parser.exit(1, "Could not stage task. Check task ID, unchanged fixtures and a new output directory.\n")


if __name__ == "__main__":
    main()
