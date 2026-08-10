import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from typing import List, Tuple, Dict, Any, Optional
import tempfile


class ThumbnailEngine:
    @staticmethod
    def extract_key_frames(video_path: str, num_frames: int = 6) -> List[str]:
        """
        Extract key candidate frames across the video using OpenCV.
        Returns list of temporary file paths for extracted images.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise RuntimeError("Invalid or empty video stream.")

        # Pick evenly spaced frame indices, avoiding very start (0%) and end (100%)
        indices = np.linspace(int(total_frames * 0.05), int(total_frames * 0.90), num_frames, dtype=int)
        extracted_paths = []

        out_dir = os.path.join(os.getcwd(), "temp_frames")
        os.makedirs(out_dir, exist_ok=True)

        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                # Convert BGR (OpenCV) to RGB (Pillow)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                frame_path = os.path.join(out_dir, f"frame_{i+1}.jpg")
                img.save(frame_path, quality=90)
                extracted_paths.append(frame_path)

        cap.release()
        return extracted_paths

    @staticmethod
    def generate_catchy_hooks(topic_or_text: str, ai_provider: Any) -> List[str]:
        """
        Generate 5 viral clickbait/hook title options for thumbnail text overlays using AI.
        """
        prompt = (
            f"Generate 5 short, high CTR, attention-grabbing thumbnail title hooks (max 4-6 words each) "
            f"for a video about: '{topic_or_text}'.\n"
            f"Make them bold, emotional, and intriguing. Return ONLY a bulleted list of 5 titles."
        )
        try:
            resp = ai_provider.generate(prompt)
            lines = [line.strip("- *•0123456789.") for line in resp.strip().split("\n") if line.strip()]
            return lines[:5] if lines else ["DON'T MISS THIS!", "UNBELIEVABLE TRUTH", "THIS CHANGES EVERYTHING", "VIRAL MOMENT!", "MUST WATCH NOW"]
        except Exception as e:
            print(f"[ThumbnailEngine] AI Hook error: {e}")
            return ["DON'T MISS THIS!", "UNBELIEVABLE TRUTH", "THIS CHANGES EVERYTHING", "VIRAL MOMENT!", "MUST WATCH NOW"]

    @staticmethod
    def apply_image_filters(
        img: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0
    ) -> Image.Image:
        """
        Apply image enhancement filters (brightness, contrast, color saturation, sharpness).
        """
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        return img

    @staticmethod
    def render_thumbnail(
        bg_image_path: str,
        header_text: str = "",
        sub_text: str = "",
        badge_text: str = "",
        aspect_ratio: str = "16:9",
        text_color: str = "#FFFF00",
        outline_color: str = "#000000",
        brightness: float = 1.0,
        contrast: float = 1.1,
        saturation: float = 1.2,
        sharpness: float = 1.2,
        output_path: str = "thumbnail.png"
    ) -> str:
        """
        Render final thumbnail image with target aspect ratio crop, text overlays, stroke, and badges.
        """
        if not os.path.exists(bg_image_path):
            raise FileNotFoundError(f"Background image not found: {bg_image_path}")

        img = Image.open(bg_image_path).convert("RGBA")

        # 1. Apply image enhancement filters
        rgb_img = img.convert("RGB")
        rgb_img = ThumbnailEngine.apply_image_filters(
            rgb_img, brightness, contrast, saturation, sharpness
        )
        img = rgb_img.convert("RGBA")

        # 2. Crop/Resize image to target aspect ratio
        if aspect_ratio == "16:9":
            target_w, target_h = 1280, 720
        elif aspect_ratio == "9:16":
            target_w, target_h = 720, 1280
        elif aspect_ratio == "1:1":
            target_w, target_h = 1080, 1080
        else:
            target_w, target_h = 1280, 720

        # Center crop to aspect ratio
        src_w, src_h = img.size
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            # Source is wider: crop sides
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, src_h))
        else:
            # Source is taller: crop top/bottom
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            img = img.crop((0, top, src_w, top + new_h))

        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # 3. Create Overlay Layer for Text & Badges
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load impact or bold sans-serif font
        font_path = None
        possible_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "C:\\Windows\\Fonts\\impact.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
        for fpath in possible_fonts:
            if os.path.exists(fpath):
                font_path = fpath
                break

        def _get_font(size):
            if font_path:
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        # Render Badge Tag if set
        if badge_text:
            badge_font = _get_font(int(target_h * 0.04))
            badge_padding = 12
            b_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
            bw = b_bbox[2] - b_bbox[0] + (badge_padding * 2)
            bh = b_bbox[3] - b_bbox[1] + (badge_padding * 2)

            bx = 30
            by = 30
            # Red/Orange badge background pill
            draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=(239, 68, 68, 240))
            draw.text((bx + badge_padding, by + badge_padding - 2), badge_text, font=badge_font, fill=(255, 255, 255, 255))

        # Render Header Text (Main Hook)
        if header_text:
            header_font_size = int(target_h * 0.10)
            h_font = _get_font(header_font_size)
            
            # Position at top-center or middle depending on subtext
            h_bbox = draw.textbbox((0, 0), header_text.upper(), font=h_font)
            hw = h_bbox[2] - h_bbox[0]
            hh = h_bbox[3] - h_bbox[1]
            hx = (target_w - hw) // 2
            hy = int(target_h * 0.15) if badge_text else int(target_h * 0.12)

            # Draw dark background box behind main header for maximum readability
            pad_x, pad_y = 20, 10
            draw.rounded_rectangle([hx - pad_x, hy - pad_y, hx + hw + pad_x, hy + hh + pad_y], radius=10, fill=(15, 15, 30, 210))

            # Draw text with outline stroke
            stroke_w = max(2, int(header_font_size * 0.05))
            draw.text((hx, hy), header_text.upper(), font=h_font, fill=text_color, stroke_width=stroke_w, stroke_fill=outline_color)

        # Render Subtext
        if sub_text:
            sub_font_size = int(target_h * 0.065)
            s_font = _get_font(sub_font_size)
            s_bbox = draw.textbbox((0, 0), sub_text, font=s_font)
            sw = s_bbox[2] - s_bbox[0]
            sh = s_bbox[3] - s_bbox[1]
            sx = (target_w - sw) // 2
            sy = int(target_h * 0.80)

            pad_x, pad_y = 16, 8
            draw.rounded_rectangle([sx - pad_x, sy - pad_y, sx + sw + pad_x, sy + sh + pad_y], radius=8, fill=(139, 92, 246, 220))
            draw.text((sx, sy), sub_text, font=s_font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill="#000000")

        # Composite image and overlay
        final_img = Image.alpha_composite(img, overlay)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        final_img.convert("RGB").save(output_path, quality=95)
        return output_path
