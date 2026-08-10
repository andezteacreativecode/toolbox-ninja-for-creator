import unittest
import os
import shutil
from PIL import Image
from core.thumbnail_engine import ThumbnailEngine


class TestThumbnailEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "temp_test_thumb")
        os.makedirs(self.test_dir, exist_ok=True)

        # Create a dummy test image
        self.test_bg = os.path.join(self.test_dir, "dummy_bg.jpg")
        img = Image.new("RGB", (1920, 1080), color=(40, 40, 80))
        img.save(self.test_bg)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_render_thumbnail_16_9(self):
        out_thumb = os.path.join(self.test_dir, "thumb_16_9.png")
        res = ThumbnailEngine.render_thumbnail(
            bg_image_path=self.test_bg,
            header_text="VIRAL SECRET UNCOVERED!",
            sub_text="Must Watch Episode 1",
            badge_text="🔥 HOT",
            aspect_ratio="16:9",
            text_color="#FFFF00",
            output_path=out_thumb
        )
        self.assertTrue(os.path.exists(res))
        out_img = Image.open(res)
        self.assertEqual(out_img.size, (1280, 720))

    def test_render_thumbnail_9_16(self):
        out_thumb = os.path.join(self.test_dir, "thumb_9_16.png")
        res = ThumbnailEngine.render_thumbnail(
            bg_image_path=self.test_bg,
            header_text="TIKTOK REELS COVER",
            aspect_ratio="9:16",
            output_path=out_thumb
        )
        self.assertTrue(os.path.exists(res))
        out_img = Image.open(res)
        self.assertEqual(out_img.size, (720, 1280))


if __name__ == "__main__":
    unittest.main()
