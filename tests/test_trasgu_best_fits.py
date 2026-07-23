import json
import sys

from trasgu.cli import best_fits

FIT = {
    "rank": 1,
    "matrix_id": 7,
    "source_aic": -12.5,
    "aic": -12.4,
    "bic": -10.0,
    "loglik": 9.0,
    "n_parameters": 3.0,
    "matrix": [[2, 2], [1, 0]],
    "model_summary": "Vinecop model summary\nfamily: clayton",
    "bicopulas": [
        {
            "tree": 1,
            "edge": 1,
            "family": "clayton",
            "rotation": 0,
            "parameters": [[2.0]],
            "tau": 0.5,
        }
    ],
}


class FakeTrasgu:
    def get_best_fits(self, count):
        assert count == 1
        return [FIT]


def test_best_fits_prints_human_output(monkeypatch, capsys):
    monkeypatch.setattr(best_fits, "Trasgu", FakeTrasgu)
    monkeypatch.setattr(sys, "argv", ["trasgu_best_fits"])

    best_fits.main()

    output = capsys.readouterr().out
    assert "Best fit #1  |  Vine ID 7" in output
    assert "Results AIC   : -12.5" in output
    assert "Refitted AIC : -12.4" in output
    assert "Structure matrix" in output
    assert "Vinecop model" in output
    assert "clayton" in output


def test_best_fits_can_write_json(monkeypatch, tmp_path):
    output_path = tmp_path / "best.json"
    monkeypatch.setattr(best_fits, "Trasgu", FakeTrasgu)
    monkeypatch.setattr(
        sys,
        "argv",
        ["trasgu_best_fits", "1", "--format", "json", "-o", str(output_path)],
    )

    best_fits.main()

    document = json.loads(output_path.read_text())
    assert document["results"][0]["matrix_id"] == 7
