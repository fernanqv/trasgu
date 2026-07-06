import pytest
import numpy as np
from pathlib import Path
from trasgu import Trasgu

def test_lazy_loading_does_not_load_on_init(tmp_path):
    # Create mock dataset
    data = np.random.rand(10, 5)  # 5 variables
    data_path = tmp_path / "data.txt"
    np.savetxt(data_path, data)

    # Create config file
    config_path = tmp_path / "trasgu.yaml"
    config_path.write_text(
        f"data_file: {data_path}\n"
        f"chunk_size: 2\n"
        f"output_dir: {tmp_path / 'fit_results'}\n"
    )

    # Instantiate config
    config = Trasgu(str(config_path))

    # Assert n_vars is resolved correctly from the header line
    assert config.n_vars == 5

    # Assert that _data is initially None (not loaded)
    assert config._data is None

    # Access data attribute (which triggers lazy loading)
    loaded_data = config.data

    # Assert data is loaded and is equal to the saved dataset
    np.testing.assert_array_equal(loaded_data, data)
    assert config._data is not None
