from __future__ import annotations

import json
import platform
import shutil
import sys
from dataclasses import dataclass
from importlib import metadata, util
from pathlib import Path


DEFAULT_DRIVE_ARTIFACT_ROOT = Path("/content/drive/MyDrive/RobotRL-Colab/artifacts")
SYNCED_RUN_ENTRIES = (
    "fetch_loop_spec.json",
    "fetch_training_spec.json",
    "preflight.json",
    "eval_results.json",
    "latest_model.zip",
    "final_model.zip",
    "success_model.zip",
    "checkpoints",
    "videos",
    "tensorboard",
    "logs",
)
PREFLIGHT_PACKAGES = (
    "gymnasium",
    "gymnasium-robotics",
    "imageio",
    "mujoco",
    "stable-baselines3",
    "tensorboard",
    "torch",
)
MIN_COLAB_PYTHON = (3, 11)


@dataclass(frozen=True)
class ColabSyncResult:
    source_run_dir: Path
    destination_run_dir: Path
    manifest_path: Path | None
    copied_entries: tuple[str, ...]
    missing_entries: tuple[str, ...]
    dry_run: bool


@dataclass(frozen=True)
class ColabPreflightResult:
    report_path: Path
    python_ok: bool
    missing_packages: tuple[str, ...]


def collect_colab_preflight() -> dict[str, object]:
    package_reports = []
    missing_packages = []
    for package_name in PREFLIGHT_PACKAGES:
        module_name = package_name.replace("-", "_")
        installed = util.find_spec(module_name) is not None
        version = _package_version(package_name) if installed else None
        if not installed:
            missing_packages.append(package_name)
        package_reports.append(
            {
                "package": package_name,
                "module": module_name,
                "installed": installed,
                "version": version,
            }
        )

    python_ok = sys.version_info[:2] >= MIN_COLAB_PYTHON
    return {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "minimum": ".".join(str(part) for part in MIN_COLAB_PYTHON),
            "ok": python_ok,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": package_reports,
        "missing_packages": missing_packages,
        "cuda": _cuda_report(),
    }


def write_colab_preflight(output_path: Path) -> ColabPreflightResult:
    report = collect_colab_preflight()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return ColabPreflightResult(
        report_path=output_path,
        python_ok=bool(report["python"]["ok"]),
        missing_packages=tuple(str(package) for package in report["missing_packages"]),
    )


def sync_colab_run_artifacts(
    run_dir: Path,
    *,
    drive_artifact_root: Path = DEFAULT_DRIVE_ARTIFACT_ROOT,
    dry_run: bool = False,
) -> ColabSyncResult:
    source_run_dir = run_dir.resolve()
    destination_run_dir = drive_artifact_root.resolve() / source_run_dir.name
    copied_entries: list[str] = []
    missing_entries: list[str] = []

    if not source_run_dir.exists():
        raise FileNotFoundError(f"run directory does not exist: {source_run_dir}")
    if not source_run_dir.is_dir():
        raise NotADirectoryError(f"run path is not a directory: {source_run_dir}")

    for entry_name in SYNCED_RUN_ENTRIES:
        source_entry = source_run_dir / entry_name
        if not source_entry.exists():
            missing_entries.append(entry_name)
            continue
        copied_entries.append(entry_name)
        if dry_run:
            continue
        destination_entry = destination_run_dir / entry_name
        if source_entry.is_dir():
            shutil.copytree(source_entry, destination_entry, dirs_exist_ok=True)
        else:
            destination_entry.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_entry, destination_entry)

    manifest = {
        "source_run_dir": str(source_run_dir),
        "destination_run_dir": str(destination_run_dir),
        "copied_entries": copied_entries,
        "missing_entries": missing_entries,
        "dry_run": dry_run,
    }
    manifest_path = None
    if not dry_run:
        manifest_dir = source_run_dir / "drive_sync"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        destination_run_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_path, destination_run_dir / "drive_sync_manifest.json")

    return ColabSyncResult(
        source_run_dir=source_run_dir,
        destination_run_dir=destination_run_dir,
        manifest_path=manifest_path,
        copied_entries=tuple(copied_entries),
        missing_entries=tuple(missing_entries),
        dry_run=dry_run,
    )


def _package_version(package_name: str) -> str | None:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def _cuda_report() -> dict[str, object]:
    if util.find_spec("torch") is None:
        return {"torch_installed": False, "available": False, "device_name": None}
    import torch

    available = bool(torch.cuda.is_available())
    return {
        "torch_installed": True,
        "available": available,
        "device_name": torch.cuda.get_device_name(0) if available else None,
        "torch_version": getattr(torch, "__version__", None),
    }
