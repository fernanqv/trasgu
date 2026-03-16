import unittest
import os
import time
from trasgu import Trasgu

class TestTrasgu(unittest.TestCase):
    """Test the Trasgu class."""

    def setUp(self):
        """Set up the test configuration."""
        self.config_path = "tests/tests_config.yaml"
        if not os.path.exists(self.config_path):
            self.fail(f"Configuration file {self.config_path} not found.")
        self.config = Trasgu(self.config_path)

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
            
        self.assertGreater(len(lines), 0, "Output file is empty")
        # Check first line - should NOT be a header, but numeric data
        first_line = lines[0].strip()
        # The expected string for the first vine in chunk 1 (vine_id 100)
        expected_string = "100,28,-10687.981736"
        self.assertEqual(first_line, expected_string)

        # Cleanup
        os.remove(output_path)
        if not os.listdir(self.config.output_dir):
            os.rmdir(self.config.output_dir)

    def test_chunk_status(self):
        """Test the get_chunk_status method."""
        chunk_index = 0
        self.config.fit_vinecop_chunk_to_file(chunk_index=chunk_index)
        
        status = self.config.get_chunk_status()
        self.assertIn(chunk_index, status["finished_chunks"])
        self.assertGreater(status["finished_chunks_count"], 0)
        
        # Cleanup
        filename = f"fit_chunk_{chunk_index:04d}_{self.config.chunk_size:05d}.csv"
        os.remove(os.path.join(self.config.output_dir, filename))
        if not os.listdir(self.config.output_dir):
            os.rmdir(self.config.output_dir)

    def test_combine_chunks(self):
        """Test the combine_chunks method."""
        # Create two small chunks
        self.config.fit_vinecop_chunk_to_file(chunk_index=0)
        self.config.fit_vinecop_chunk_to_file(chunk_index=1)
        
        combined_file = "combined_test.csv"
        combined_path = self.config.combine_chunks(output_filename=combined_file, delete_chunks=True)
        
        self.assertTrue(os.path.exists(combined_path))
        
        with open(combined_path, "r") as f:
            lines = f.readlines()
        
        # Header + at least two chunks each of size config.chunk_size
        # (Though in our tests chunk_size might be small)
        self.assertEqual(lines[0].strip(), "vine_id,n_parameters,aic")
        
        # Cleanup
        os.remove(combined_path)
        if not os.listdir(self.config.output_dir):
            os.rmdir(self.config.output_dir)


    def test_chunk_matrices_range(self):
        """Test 6: tuple_range has to be (100,199)."""
        tuple_range = self.config.print_chunk_matrices_range(1)
        self.assertEqual(tuple_range, (100, 199))

    def test_fit_all_chunks(self):
        """Test the fit_all_chunks method."""
        try:
            # Process only 2 chunks for the test and combine
            self.config.fit_all_chunks(skip_finished=False, max_chunks=2, combine_at_end=True)
            
            # Check if both files exist
            for i in range(2):
                filename = f"fit_chunk_{i:04d}_{self.config.chunk_size:05d}.csv"
                path = os.path.join(self.config.output_dir, filename)
                self.assertTrue(os.path.exists(path), f"Chunk {i} file not found")
                os.remove(path)
            
            # Check combined file
            combined_path = os.path.join(self.config.output_dir, "final_results.csv")
            self.assertTrue(os.path.exists(combined_path), "Combined file not found")
            os.remove(combined_path)
        finally:
            pass
            
        if os.path.exists(self.config.output_dir) and not os.listdir(self.config.output_dir):
            os.rmdir(self.config.output_dir)


if __name__ == "__main__":
    unittest.main()
