from tools import read_file
import pytest

def test_truncation(tmp_path, monkeypatch):
    monkeypatch.setattr(read_file, "MAX_CHARS", 10)
    f = tmp_path / "long.txt"
    f.write_text("a" * 50)
    out = read_file.run(path=str(f))
    assert out.startswith("a" * 10)
    assert "truncated" in out
    assert "50" in out