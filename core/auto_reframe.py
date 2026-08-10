import cv2
import mediapipe as mp
import numpy as np

class AutoReframe:
    def __init__(self, aspect_ratio="9:16"):
        self.aspect_ratio = aspect_ratio
        
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

    def calculate_crop_window(self, video_path: str, start_time: float, end_time: float):
        """
        Calculates the average center of the face(s) in the segment to determine the crop window.
        Returns a string for FFmpeg crop filter like "crop=W:H:X:Y" or None if no face found.
        """
        if self.aspect_ratio != "9:16":
            return None # We only auto-reframe for vertical video

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        target_width = int(height * 9 / 16)
        if target_width > width:
            target_width = width
            
        # Target frame range
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        face_centers = []
        frame_count = 0
        
        # Sample every Nth frame to speed up processing
        sample_rate = max(1, int(fps / 5)) 
        
        while cap.isOpened() and cap.get(cv2.CAP_PROP_POS_FRAMES) <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % sample_rate == 0:
                # Convert the BGR image to RGB
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(image_rgb)
                
                if results.detections:
                    # Get the most prominent face (largest bounding box)
                    largest_face = max(results.detections, 
                                     key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
                    
                    bbox_c = largest_face.location_data.relative_bounding_box
                    x_center = int((bbox_c.xmin + bbox_c.width / 2) * width)
                    face_centers.append(x_center)
                    
            frame_count += 1
            
        cap.release()
        
        if not face_centers:
            # Default center crop if no face found
            x_crop = (width - target_width) // 2
        else:
            # Smooth tracking: use median of face centers to avoid jitter
            avg_x = int(np.median(face_centers))
            
            # Calculate crop X ensuring it doesn't go out of bounds
            x_crop = avg_x - (target_width // 2)
            x_crop = max(0, min(x_crop, width - target_width))
            
        return f"crop={target_width}:{height}:{x_crop}:0"
