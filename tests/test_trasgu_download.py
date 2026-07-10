import numpy as np
from trasgu.cli import download_zarr as trasgu_download_zarr

def test_trasgu_download_basic(tmp_path, monkeypatch):
    dest_dir = tmp_path
    zarr_dir = dest_dir / "chimera.zarr"

    # Mock remote group
    class MockArray:
        def __init__(self, shape, chunks, dtype):
            self.shape = shape
            self.chunks = chunks
            self.dtype = dtype

    class MockRemoteGroup:
        def __contains__(self, name):
            return name in ("matrices4", "matrices5")
        
        def __getitem__(self, name):
            if name == "matrices4":
                return MockArray((24, 4, 4), (100, 4, 4), np.uint8)
            elif name == "matrices5":
                return MockArray((480, 5, 5), (480, 5, 5), np.uint8)
            raise KeyError(name)

    mock_remote = MockRemoteGroup()
    mock_local = {}
    local_stores = []

    # Mock open_group
    def mock_open_group(store, mode):
        if store == "http://example.invalid/chimera.zarr" or hasattr(store, "fs"):
            return mock_remote
        else:
            local_stores.append(store)
            # Local group
            class MockLocalGroup:
                def __contains__(self, name):
                    return name in mock_local
                def __getitem__(self, name):
                    return mock_local[name]
                def create_array(self, name, shape, chunks, dtype, overwrite):
                    mock_local[name] = MockArray(shape, chunks, dtype)
                    # Add array item setter mock to allow slicing assignment
                    class SlicedArray:
                        def __setitem__(self, key, value):
                            pass
                    return SlicedArray()
            return MockLocalGroup()

    monkeypatch.setattr(trasgu_download_zarr.zarr, "open_group", mock_open_group)
    monkeypatch.setattr(trasgu_download_zarr.sys, "argv", [
        "trasgu_download_zarr",
        str(dest_dir),
        "--vars", "4",
        "--url", "http://example.invalid/chimera.zarr"
    ])

    # Run the main function
    trasgu_download_zarr.main()

    # Verify matrices4 was created in mock local store
    assert "matrices4" in mock_local
    assert local_stores == [str(zarr_dir)]
