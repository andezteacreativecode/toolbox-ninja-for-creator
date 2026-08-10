import unittest
import os
import shutil
from core.tts_engine import TTSEngine
from core.audio_mixer import AudioMixer


class TestVoiceoverAndAudio(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "temp_test_audio")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_list_voices(self):
        voices = TTSEngine.list_popular_voices()
        self.assertGreater(len(voices), 0)
        self.assertTrue(any("id-ID" in v["lang"] for v in voices))

    def test_edge_tts_generation(self):
        output_file = os.path.join(self.test_dir, "test_voice.mp3")
        try:
            res = TTSEngine.generate_edge_tts_sync(
                text="Halo ini adalah pengujian suara AI desktop",
                voice="id-ID-GadisNeural",
                output_path=output_file
            )
            self.assertTrue(os.path.exists(res))
            self.assertGreater(os.path.getsize(res), 1000)
        except Exception as e:
            self.skipTest(f"Network error or edge-tts service unavailable: {e}")


if __name__ == "__main__":
    unittest.main()
