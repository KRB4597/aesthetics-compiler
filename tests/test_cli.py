"""CLI smoke tests — the CLI was previously 0% covered.

Uses Typer's in-process runner for command coverage.  (The `python -m`
entrypoint itself is regression-tested in test_regressions.py.)
"""
import json

from typer.testing import CliRunner

from aesthetics_compiler.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "aesthetics-compiler" in result.stdout


def test_cli_compile_writes_ir(tmp_path):
    src = tmp_path / "art.txt"
    src.write_text("A balanced, symmetrical, harmonious composition.")
    out = tmp_path / "art.ir.json"
    result = runner.invoke(app, ["compile", str(src), "--out", str(out), "--quiet"])
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"]
    assert data["projections"]


def test_cli_compile_invalid_projection(tmp_path):
    src = tmp_path / "art.txt"
    src.write_text("A painting.")
    result = runner.invoke(app, ["compile", str(src), "--projection", "bogus"])
    assert result.exit_code != 0


def test_cli_report_roundtrip(tmp_path):
    src = tmp_path / "art.txt"
    src.write_text("A vibrant, ordered composition.")
    out = tmp_path / "art.ir.json"
    runner.invoke(app, ["compile", str(src), "--out", str(out), "--quiet"])
    result = runner.invoke(app, ["report", str(out)])
    assert result.exit_code == 0
