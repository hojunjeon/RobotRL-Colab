import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robotrl.colab import _validate_drive_artifact_root, sync_colab_run_artifacts


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
        self.assertTrue(any("!git pull --ff-only\n" in source for source in cell_sources))
        self.assertTrue(any("!git rev-parse HEAD" in source for source in cell_sources))
        self.assertFalse(any("git pull --ff-only || true" in source for source in cell_sources))
        self.assertTrue(any("--max-iterations 1" in source for source in cell_sources))
        self.assertTrue(any("--resume-from {RESUME_FROM}" in source for source in cell_sources))
        self.assertFalse(any("\\n" in part for cell in notebook["cells"] for part in cell.get("source", [])))

    def test_docs_define_colab_primary_r30o_source_edit_contract(self):
        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")
        r30o_lab = (root / "docs" / "colab" / "r30o_lab.md").read_text(encoding="utf-8")
        runbook = (root / "docs" / "colab" / "runbook.md").read_text(encoding="utf-8")
        docs = "\n".join([readme, r30o_lab, runbook])

        self.assertIn("Colab-primary", docs)
        self.assertIn("local Windows checkout is optional", docs)
        self.assertIn("Edit files inside `/content/RobotRL-Colab` through Colab MCP.", r30o_lab)
        self.assertIn("commit and push from Colab immediately", docs)
        self.assertIn("Drive = durable artifact store", readme)
        self.assertIn("return within `.codex/config.toml` `tool_timeout_sec`", docs)
        self.assertIn("live tool-list check is mandatory", docs)
        self.assertIn("nonblocking visual approval", docs)
        self.assertIn("committed project-scoped `.codex/config.toml`", docs)
        self.assertNotIn("make the smallest code/config change locally", r30o_lab)
        self.assertNotIn("make them locally", r30o_lab)

    def test_project_colab_mcp_config_is_committable_and_sanitized(self):
        root = Path(__file__).resolve().parents[1]
        config_path = root / ".codex" / "config.toml"

        self.assertTrue(config_path.exists())
        tracked = subprocess.run(
            ["git", "ls-files", "--", ".codex/config.toml"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn(".codex/config.toml", tracked.stdout.splitlines())
        config = config_path.read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.colab-mcp]", config)
        self.assertIn("git+https://github.com/googlecolab/colab-mcp", config)
        self.assertNotIn("api_key", config.lower())
        self.assertNotIn("token", config.lower())
        self.assertNotIn("secret", config.lower())

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

            result = sync_colab_run_artifacts(
                run_dir,
                drive_artifact_root=drive_root,
                allow_unmounted_drive=True,
            )

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

    def test_sync_rejects_default_drive_root_without_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_001_stage1_strict_withdraw_seed7"
            run_dir.mkdir()
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                sync_colab_run_artifacts(run_dir)

    def test_sync_rejects_default_drive_root_with_unmounted_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_001_stage1_strict_withdraw_seed7"
            run_dir.mkdir()
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "/content/drive"):
                sync_colab_run_artifacts(run_dir, allow_unmounted_drive=True)

    def test_sync_rejects_colab_local_drive_lookalike_without_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_001_stage1_strict_withdraw_seed7"
            run_dir.mkdir()
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "/content/drive"):
                sync_colab_run_artifacts(
                    run_dir,
                    drive_artifact_root=Path("/content/gdrive/MyDrive/RobotRL-Colab/artifacts"),
                )

            _validate_drive_artifact_root(
                Path("/content/gdrive/MyDrive/RobotRL-Colab/artifacts"),
                allow_unmounted_drive=True,
            )

    def test_sync_rejects_destination_collision_without_allow_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001_stage1_strict_withdraw_seed7"
            drive_root = tmp_path / "drive" / "artifacts"
            run_dir.mkdir()
            (run_dir / "eval_results.json").write_text("[]", encoding="utf-8")
            (drive_root / run_dir.name).mkdir(parents=True)

            with self.assertRaises(FileExistsError):
                sync_colab_run_artifacts(
                    run_dir,
                    drive_artifact_root=drive_root,
                    allow_unmounted_drive=True,
                )

            result = sync_colab_run_artifacts(
                run_dir,
                drive_artifact_root=drive_root,
                allow_unmounted_drive=True,
                allow_merge=True,
            )

            self.assertTrue((result.destination_run_dir / "eval_results.json").exists())

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
                    "--allow-unmounted-drive",
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
