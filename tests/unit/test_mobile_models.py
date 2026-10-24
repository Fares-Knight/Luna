"""Les OBJ livrés restent reproductibles depuis les sources éditables."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def test_mobile_models_are_the_exact_deterministic_exports(tmp_path):
    root = Path(__file__).resolve().parents[2]
    spec = spec_from_file_location("mobile_models", root / "tools/generate_mobile_models.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DESTINATION = tmp_path
    module.build()
    shipped = root / "android/app/src/main/assets/models"
    expected = {f"flower_{index}.obj" for index in range(7)} | {"scissors.obj", "board.obj"}
    assert {path.name for path in tmp_path.iterdir()} == expected
    for name in expected:
        assert (tmp_path / name).read_bytes() == (shipped / name).read_bytes()
