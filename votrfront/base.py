from pathlib import Path


ROOT_PATH = Path(__file__).resolve().parent.parent


def var_path(*path_segments: Path | str) -> Path:
    return ROOT_PATH.joinpath('var', *path_segments)

    # NOTE: For future reference, if we later want to customize var_path within
    # unit tests, this should work:
    #     monkeypatch.setattr('votrfront.base.ROOT_PATH', tmp_path)
    #     (tmp_path / 'var').mkdir()
