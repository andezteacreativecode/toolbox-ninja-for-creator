import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory
from core.downloader import VideoDownloader
from core.transcriber import VideoTranscriber
from core.moment_detector import MomentDetector
from core.clipper import VideoClipper

def test_settings():
    print("[TEST] Testing SettingsManager...")
    mgr = SettingsManager()
    data = mgr.load()
    assert "active_provider" in data
    assert "providers" in data
    assert "ollama" in data["providers"]
    assert "9router" in data["providers"]
    print("  ✅ SettingsManager OK")

def test_providers():
    print("[TEST] Testing AI Provider Factory...")
    mgr = SettingsManager()
    ollama_cfg = mgr.data["providers"]["ollama"]
    p1 = ProviderFactory.get_provider("ollama", ollama_cfg)
    ok1, msg1 = p1.test_connection()
    print(f"  Ollama status: {ok1} -> {msg1}")

    router_cfg = mgr.data["providers"]["9router"]
    p2 = ProviderFactory.get_provider("9router", router_cfg)
    ok2, msg2 = p2.test_connection()
    print(f"  9router status: {ok2} -> {msg2}")
    print("  ✅ Provider Factory OK")

def test_detector_heuristic():
    print("[TEST] Testing MomentDetector Fallback Heuristic...")
    mgr = SettingsManager()
    ollama_cfg = mgr.data["providers"]["ollama"]
    p1 = ProviderFactory.get_provider("ollama", ollama_cfg)
    detector = MomentDetector(p1)
    
    segments = [
        {"start": 0.0, "end": 10.0, "text": "Halo selamat datang di podcast hari ini."},
        {"start": 10.0, "end": 45.0, "text": "Ini adalah momen yang sangat lucu dan mengagetkan sekali!"},
        {"start": 45.0, "end": 90.0, "text": "Penutup video dan kesimpulan akhir."}
    ]
    
    clips = detector.detect_viral_moments(
        video_path="dummy.mp4",
        segments=segments,
        num_clips=2,
        target_duration=30
    )
    assert len(clips) == 2
    assert clips[0]['duration'] > 0
    print(f"  Clips generated: {len(clips)} clips")
    for c in clips:
        print(f"   - {c['title']} [{c['start']}s - {c['end']}s] score: {c['score']}")
    print("  ✅ MomentDetector Heuristic OK")

if __name__ == "__main__":
    test_settings()
    test_providers()
    test_detector_heuristic()
    print("\n🎉 ALL UNIT TESTS PASSED!")
