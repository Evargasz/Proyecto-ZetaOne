import unittest
import os
import tempfile
from explorador import explorar_sd_folder

class TestExplorador(unittest.TestCase):
    def setUp(self):
        self.dir_temp = tempfile.TemporaryDirectory()
        self.path = self.dir_temp.name
        # Crea algunos archivos de prueba
        with open(os.path.join(self.path, "SD1_test.sp"), "w") as f:
            f.write("-- demo")
        with open(os.path.join(self.path, "test.sql"), "w") as f:
            f.write("-- demo")
        os.mkdir(os.path.join(self.path, "SDextra"))
        with open(os.path.join(self.path, "SDextra", "extra.sp"), "w") as f:
            f.write("-- demo")
    def tearDown(self):
        self.dir_temp.cleanup()
    def test_explora_unico(self):
        res = explorar_sd_folder(self.path)
        self.assertTrue(any(a['nombre_archivo'].endswith('.sp') for a in res))
    def test_explora_multi(self):
        res = explorar_sd_folder(self.path, multi_sd=True)
        self.assertTrue(isinstance(res, list))

if __name__ == "__main__":
    unittest.main()