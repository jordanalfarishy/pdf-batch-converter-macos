import tempfile
import threading
import unittest
from pathlib import Path

import pikepdf
from PIL import Image

from converter_core import convert_folder, get_images, list_subfolders


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "input"
        self.output = self.root / "output"
        self.input.mkdir()
        self.output.mkdir()
        self.cancel = threading.Event()

    def image(self, folder, name, mode="RGB"):
        path = folder / name
        color = (255, 0, 0, 180) if mode == "RGBA" else (255, 0, 0)
        Image.new(mode, (80, 40), color).save(path)
        return path

    def test_mixed_formats_sort_and_skip_bad_image(self):
        folder = self.input / "Album"
        folder.mkdir()
        self.image(folder, "10.webp")
        self.image(folder, "2.png", "RGBA")
        self.image(folder, "1.jpg")
        (folder / "3.jpg").write_text("not an image")
        (folder / "notes.txt").write_text("ignored")

        self.assertEqual([Path(p).name for p in get_images(str(folder))],
                         ["1.jpg", "2.png", "3.jpg", "10.webp"])
        result = convert_folder(str(folder), str(self.output), "None", self.cancel)
        self.assertEqual((result.status, result.page_count, result.skipped_images),
                         ("ok", 3, 1))
        with pikepdf.open(self.output / result.output_name) as pdf:
            self.assertEqual(len(pdf.pages), 3)

    def test_existing_pdf_and_sanitized_name_collision_are_preserved(self):
        first = self.input / "A:B"
        second = self.input / "AB"
        first.mkdir()
        second.mkdir()
        self.image(first, "1.jpg")
        self.image(second, "1.jpg")
        original = self.output / "AB.pdf"
        original.write_bytes(b"existing")
        results = [convert_folder(str(folder), str(self.output), "Medium", self.cancel)
                   for folder in (first, second)]
        self.assertEqual([result.status for result in results], ["ok", "ok"])
        self.assertEqual([result.output_name for result in results], ["AB (2).pdf", "AB (3).pdf"])
        self.assertEqual(original.read_bytes(), b"existing")

    def test_cancel_and_empty_folder_leave_no_pdf(self):
        folder = self.input / "Empty"
        folder.mkdir()
        self.assertEqual(convert_folder(str(folder), str(self.output), "Low", self.cancel).status,
                         "skipped")
        self.image(folder, "1.jpg")
        self.cancel.set()
        self.assertEqual(convert_folder(str(folder), str(self.output), "Low", self.cancel).status,
                         "cancelled")
        self.assertEqual(list(self.output.iterdir()), [])

    def test_hidden_and_symlink_folders_are_ignored(self):
        self.image_folder("2")
        self.image_folder("10")
        self.image_folder(".hidden")
        (self.input / "alias").symlink_to(self.input / "2", target_is_directory=True)
        self.assertEqual([Path(p).name for p in list_subfolders(str(self.input))], ["2", "10"])

    def image_folder(self, name):
        folder = self.input / name
        folder.mkdir()
        self.image(folder, "1.jpg")


if __name__ == "__main__":
    unittest.main()
