import os
import math
from pathlib import Path

class SubtitleBurner:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _convert_color_to_ass(self, hex_color: str) -> str:
        """Convert #RRGGBB to ASS color format &HBBGGRR&"""
        if not hex_color.startswith('#'):
            return "&H00FFFFFF&" # Default white
        
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
            return f"&H00{b}{g}{r}&"
        return "&H00FFFFFF&"

    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format h:mm:ss.cs"""
        h = int(seconds / 3600)
        m = int((seconds % 3600) / 60)
        s = seconds % 60
        cs = int(round(math.modf(s)[0] * 100))
        return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"

    def generate_ass_file(self, clip_info: dict, settings: dict, clip_index: int, video_width: int, video_height: int) -> str:
        ass_path = self.temp_dir / f"subs_clip_{clip_index}.ass"
        
        # Parse settings
        font_name = settings.get("font_family", "Arial")
        font_size = settings.get("font_size", 48)
        text_color = self._convert_color_to_ass(settings.get("text_color", "#ffffff"))
        hl_color = self._convert_color_to_ass(settings.get("highlight_color", "#ffea00"))
        bold = "-1" if settings.get("style_bold", True) else "0"
        italic = "-1" if settings.get("style_italic", False) else "0"
        
        outline = "2" if settings.get("stroke", True) else "0"
        outline_color = "&H00000000&" # Black outline
        
        # Position mapping
        pos_str = settings.get("position", "center").lower()
        if pos_str == "top":
            alignment = "8" # Top center
            margin_v = "40"
        elif pos_str == "bottom":
            alignment = "2" # Bottom center
            margin_v = "80"
        else:
            alignment = "5" # Middle center
            margin_v = "0"
            
        animation = settings.get("animation", "word_highlight")

        # Create ASS Header
        ass_content = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "WrapStyle: 1",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{font_name},{font_size},{text_color},&H000000FF&,{outline_color},&H90000000&,{bold},{italic},0,0,100,100,0,0,3,{outline},0,{alignment},20,20,{margin_v},1",
            f"Style: Highlight,{font_name},{font_size},{hl_color},&H000000FF&,{outline_color},&H90000000&,{bold},{italic},0,0,100,100,0,0,3,{outline},0,{alignment},20,20,{margin_v},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        # Get words related to this clip
        words = clip_info.get("words", [])
        clip_start = clip_info.get("start", 0)
        
        # If no word-level timestamps, just show the whole text
        if not words or animation == "none":
            start_t = self._format_ass_time(0)
            end_t = self._format_ass_time(clip_info.get("duration", 30))
            text = clip_info.get("text", "No transcript")
            ass_content.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{text}")
        else:
            # Group words into chunks (e.g., max 4-6 words per screen)
            chunk_size = 5
            chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
            
            for chunk in chunks:
                if not chunk: continue
                
                chunk_start_abs = chunk[0]['start']
                chunk_end_abs = chunk[-1]['end']
                
                # Relativize to clip start
                chunk_start_rel = max(0, chunk_start_abs - clip_start)
                chunk_end_rel = max(0, chunk_end_abs - clip_start)
                
                if chunk_end_rel <= 0: continue
                
                full_text = " ".join([w['text'] for w in chunk])
                
                if animation == "word_highlight":
                    # Generate a dialogue line for each word being highlighted
                    for i, focus_word in enumerate(chunk):
                        word_start_abs = focus_word['start']
                        word_end_abs = focus_word['end']
                        
                        word_start_rel = max(0, word_start_abs - clip_start)
                        word_end_rel = max(0, word_end_abs - clip_start)
                        
                        start_t = self._format_ass_time(word_start_rel)
                        end_t = self._format_ass_time(word_end_rel)
                        
                        # Build formatted text with {\c&H...&} override for highlight color
                        styled_text = ""
                        for j, w in enumerate(chunk):
                            if i == j:
                                styled_text += f"{{\\c{hl_color}}}{w['text']}{{\\c{text_color}}} "
                            else:
                                styled_text += f"{w['text']} "
                        
                        styled_text = styled_text.strip()
                        ass_content.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{styled_text}")
                elif animation == "fade":
                     start_t = self._format_ass_time(chunk_start_rel)
                     end_t = self._format_ass_time(chunk_end_rel)
                     ass_content.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{{\\fad(200,200)}}{full_text}")
                else: # pop or other
                     start_t = self._format_ass_time(chunk_start_rel)
                     end_t = self._format_ass_time(chunk_end_rel)
                     ass_content.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{full_text}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_content))
            
        return str(ass_path.absolute())
