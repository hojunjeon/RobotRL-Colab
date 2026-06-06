import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robotrl.colab import sync_colab_run_artifacts


class ColabArtifactSyncTest(unittest.TestCase):
    def test_colab_notebook_keeps_fetch_install_dry_run_and_sync_cells(self):
        notebook_path = Path(__file__).resolve().parents[1] / "notebooks" / "RobotRL_Colab_Run.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        cell_sources = ["".join(cell.get("source", [])) for cell in notebook["cells"]]

        self.assertTrue(any("drive.mount" in source for source in cell_sources))
        self.assertTrue(any("python -m pip install -e '.[fetch]'" in source for source in cell_sources))
        self.assertTrue(any("python -m robotrl.cli colab-preflight" in source for source in cell_sources))
        self.assertTrue(any("python -m robotrl.cli fetch-loop --dry-run" in source for source in cell_sources))
        self.assertTrue(any("python -m robotrl.cli colab-sync" in source for source in cell_sources))

    def test_sync_copies_known_run_artifacts_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001_stage1_strict_withdraw_seed7"
            drive_root = tmp_path / "drive" / "artifacts"
            (run_dir / "checkpoints").mkdir(parents=True)
            (run_dir / "videos").mkdir()
            (run_dir / "tensorboard").mkdir()
            (run_dir / "fetch_loop_spec.json").write_text("{}", encoding="utf-8")
            (run_dir / "preflight.json").write_text("{}", encoding="utf-8")
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")
            (run_dir / "checkpoints" / "latest.zip").write_text("checkpoint", encoding="utf-8")
            (run_dir / "videos" / "rollout.gif").write_bytes(b"GIF89a")
            (run_dir / "tensorboard" / "events.out.tfevents.test").write_text("tb", encoding="utf-8")

            result = sync_colab_run_artifacts(run_dir, drive_artifact_root=drive_root)

            destination = drive_root / run_dir.name
            self.assertEqual(result.destination_run_dir, destination)
            self.assertIn("fetch_loop_spec.json", result.copied_entries)
            self.assertIn("checkpoints", result.copied_entries)
            self.assertTrue((destination / "fetch_loop_spec.json").exists())
            self.assertTrue((destination / "preflight.json").exists())
            self.assertTrue((destination / "eval_results.json").exists())
            self.assertTrue((destination / "checkpoints" / "latest.zip").exists())
            self.assertTrue((destination / "videos" / "rollout.gif").exists())
            self.assertTrue((destination / "tensorboard" / "events.out.tfevents.test").exists())
            self.assertTrue((destination / "drive_sync_manifest.json").exists())
            self.assertIsNotNone(result.manifest_path)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["destination_run_dir"], str(destination))
            self.assertFalse(manifest["dry_run"])

    def test_dry_run_reports_without_copying(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "dry_run_stage1_strict_withdraw_seed7"
            drive_root = tmp_path / "drive" / "artifacts"
            run_dir.mkdir()
            (run_dir / "fetch_loop_spec.json").write_text("{}", encoding="utf-8")

            result = sync_colab_run_artifacts(run_dir, drive_artifact_root=drive_root, dry_run=True)

            self.assertTrue(result.dry_run)
            self.assertIn("fetch_loop_spec.json", result.copied_entries)
            self.assertIsNone(result.manifest_path)
            self.assertFalse((drive_root / run_dir.name).exists())

    def test_cli_colab_sync_prints_destination_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001_stage1_strict_withdraw_seed7"
            drive_root = tmp_path / "drive" / "artifacts"
            run_dir.mkdir()
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "robotrl.cli",
                    "colab-sync",
                    "--run-dir",
                    str(run_dir),
                    "--drive-artifact-root",
                    str(drive_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn(f"destination={drive_root / run_dir.name}", completed.stdout)
            self.assertIn("copied=eval_results.json", completed.stdout)
            self.assertIn("manifest=", completed.stdout)

    def test_cli_colab_preflight_writes_runtime_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "preflight.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "robotrl.cli",
                    "colab-preflight",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("preflight=", completed.stdout)
            self.assertIn("python", report)
            self.assertIn("packages", report)
            self.assertIn("cuda", report)


if __name__ == "__main__":
    unittest.main()
