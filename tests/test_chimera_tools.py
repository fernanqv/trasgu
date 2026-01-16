import unittest
import os
import time
from chimera_vines import ChimeraVines

class TestChimeraVines(unittest.TestCase):
    """Test the ChimeraVines class."""

    def setUp(self):
        """Set up the test configuration."""
        self.config_path = "tests/tests_config.yaml"
        if not os.path.exists(self.config_path):
            self.fail(f"Configuration file {self.config_path} not found.")
        self.config = ChimeraVines(self.config_path)

    def test_measure_fitting_time(self):
        """Test 1: measure_fitting_time has to take less than 1 minute."""
        start_time = time.time()
        self.config.measure_fitting_time()
        elapsed_time = time.time() - start_time
        self.assertLess(elapsed_time, 60, "measure_fitting_time took longer than 1 minute")

    def test_number_of_chimera_matrices(self):
        """Test 2: n has to be equal to 660602880."""
        n = self.config.get_number_of_chimera_matrices()
        self.assertEqual(n, 660602880)

    def test_number_of_chunks(self):
        """Test 3: n_chunks has to be equal to 6606029."""
        n_chunks = self.config.get_number_of_chunks()
        self.assertEqual(n_chunks, 6606029)

    def test_chunk_id_from_matrix_id(self):
        """Test 4: chunk_id has to be equal to 60000."""
        chunk_id = self.config.get_id_chunk_from_matrix_id(matrix_id=6000000)
        self.assertEqual(chunk_id, 60000)

    def test_fit_vinecop_chunk_to_file(self):
        """Test 5: Verify output of fit_vinecop_chunk_to_file."""
        chunk_index = 1
        
        # Measure time as requested
        start_time = time.time()
        self.config.fit_vinecop_chunk_to_file(chunk_index=chunk_index)
        elapsed_time = time.time() - start_time
        print(f"Time taken for fit_vinecop_chunk_to_file: {elapsed_time:.4f} seconds")
        
        # Check file content
        filename = f"fit_chunk_{chunk_index:04d}_{self.config.chunk_size:05d}.csv"
        output_path = os.path.join(self.config.output_dir, filename)
        
        self.assertTrue(os.path.exists(output_path), f"Output file {output_path} does not exist")
        
        with open(output_path, "r") as f:
            lines = f.readlines()
            
        self.assertGreater(len(lines), 1, "Output file is empty")
        # Check second line
        second_line = lines[1].strip()
        expected_string = "100,28,-10687.981736"
        self.assertEqual(second_line, expected_string)

        # Remove the file and folder after test
        os.remove(output_path)
        os.rmdir(self.config.output_dir)


    def test_chunk_matrices_range(self):
        """Test 6: tuple_range has to be (100,199)."""
        tuple_range = self.config.print_chunk_matrices_range(1)
        self.assertEqual(tuple_range, (100, 199))

if __name__ == "__main__":
    unittest.main()
