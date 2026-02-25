# object_detector.py
# This module uses YOLOv8 AI to detect objects in camera frames
# Updated to include paper detection using contour analysis

import cv2
from ultralytics import YOLO
import numpy as np

class ObjectDetector:
    """
    A class to detect objects using YOLOv8, with added paper detection
    """
    
    def __init__(self):
        """
        Initialize the YOLO model and paper detection settings
        """
        print("🤖 Loading YOLOv8 AI model...")
        print("(First time may take 1-2 minutes to download model)")
        
        # Load YOLOv8 nano model (smallest, fastest)
        self.model = YOLO('yolov8n.pt')
        
        print("✅ YOLO model loaded successfully!")
        
        # Define which objects we care about for garbage detection
        # 'bottle' for water bottles, 'cup' for cups, etc.
        # 'paper' removed since we detect it separately with contours
        self.garbage_objects = [
            'bottle', 'cup', 'fork', 'knife', 'spoon', 'bowl',
            'banana', 'apple', 'sandwich', 'orange', 'broccoli',
            'carrot', 'pizza', 'donut', 'cake', 'backpack',
            'handbag', 'suitcase', 'frisbee', 'sports ball', 'book'
        ]
        
        # Class names that YOLO can detect (80 objects total)
        self.class_names = self.model.names
        
        # Settings for paper detection
        self.paper_min_area = 500  # Minimum area for paper contours
        self.paper_max_area = 50000  # Maximum area
        self.paper_brightness_threshold = 120  # Minimum brightness for white paper
        
        # Store paper boxes for reuse
        self.current_paper_boxes = []
    
    def detect_paper_contours(self, frame):
        """
        Detect paper-like objects using contour analysis.
        
        Args:
            frame: Input image (numpy array)
        
        Returns:
            paper_boxes: List of bounding boxes [x1, y1, x2, y2] for detected paper
        """
        # Convert to grayscale and apply blur to reduce noise
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection using Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        paper_boxes = []
        for contour in contours:
            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular (4 sides)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if self.paper_min_area < area < self.paper_max_area:
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    
                    # Filter for reasonable aspect ratios (rectangular, not too extreme)
                    if 0.3 < aspect_ratio < 3.0:
                        # Check brightness of the region (for white paper)
                        roi = frame[y:y+h, x:x+w]
                        if roi.size > 0:
                            mean_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
                            if mean_brightness > self.paper_brightness_threshold:
                                paper_boxes.append([x, y, x+w, y+h])
        
        return paper_boxes
    
    def detect_objects(self, frame):
        """
        Detect objects in a frame using YOLO and paper detection
        
        Args:
            frame: Image from camera (numpy array)
            
        Returns:
            results: Detection results from YOLO
            annotated_frame: Frame with boxes and labels drawn (including paper)
        """
        # Run YOLO detection
        results = self.model(frame, conf=0.5, verbose=False)
        
        # Get the annotated frame (with YOLO boxes drawn)
        annotated_frame = results[0].plot()
        
        # Run paper detection on the original frame
        self.current_paper_boxes = self.detect_paper_contours(frame)
        
        # Draw paper detections on the annotated frame (blue boxes)
        for box in self.current_paper_boxes:
            cv2.rectangle(annotated_frame, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)  # Blue rectangle
            cv2.putText(annotated_frame, "paper", (box[0], box[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)  # Blue label
        
        return results, annotated_frame
    
    def extract_detections(self, results):
        """
        Extract useful information from YOLO results and add paper detections
        
        Args:
            results: YOLO detection results
            
        Returns:
            detections: List of dictionaries containing detection info (including paper)
        """
        detections = []
        
        # Extract YOLO detections
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get object class ID
                class_id = int(box.cls[0])
                
                # Get object name
                object_name = self.class_names[class_id]
                
                # Get confidence score
                confidence = float(box.conf[0])
                
                # Get box coordinates [x1, y1, x2, y2]
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                
                # Check if this object is potential garbage
                is_garbage = object_name in self.garbage_objects
                
                # Store detection info
                detection_info = {
                    'object': object_name,
                    'confidence': round(confidence * 100, 2),  # Convert to percentage
                    'box': [x1, y1, x2, y2],
                    'is_garbage': is_garbage
                }
                
                detections.append(detection_info)
        
        # Add paper detections (reuse from detect_objects)
        # Uncomment for debug: print(f"Adding {len(self.current_paper_boxes)} paper detections")
        for box in self.current_paper_boxes:
            detections.append({
                'object': 'paper',
                'confidence': 75.0,  # Fixed confidence for rule-based detection
                'box': box,
                'is_garbage': True  # Always flag paper as garbage
            })
        
        # Uncomment for debug: print(f"Total detections: {len(detections)}")
        return detections


def test_object_detection():
    """
    Test function to check if object detection works with camera
    """
    print("\n" + "="*60)
    print("TESTING OBJECT DETECTION WITH CAMERA")
    print("="*60 + "\n")
    
    # Import camera module
    from camera_module import CameraModule
    
    # Initialize camera
    cam = CameraModule(camera_index=0)
    
    # Initialize object detector
    detector = ObjectDetector()
    
    print("\n📹 Starting live object detection...")
    print("👉 Show objects to the camera (bottles, cups, paper, etc.)")
    print("Press 'q' to quit\n")
    
    frame_count = 0
    
    while True:
        # Read frame from camera
        success, frame = cam.read_frame()
        
        if not success:
            print("❌ Failed to read frame")
            break
        
        frame_count += 1
        
        # Detect objects in the frame
        results, annotated_frame = detector.detect_objects(frame)
        
        # Extract detection information
        detections = detector.extract_detections(results)
        
        # Add instruction text to frame
        cv2.putText(
            annotated_frame,
            "Press 'q' to quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        
        # Add detection count
        cv2.putText(
            annotated_frame,
            f"Objects detected: {len(detections)}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Print detections to terminal (every 30 frames to avoid spam)
        if frame_count % 30 == 0 and len(detections) > 0:
            print(f"\n📊 Frame {frame_count} - Detected:")
            for det in detections:
                garbage_marker = "🗑️" if det['is_garbage'] else "✅"
                print(f"  {garbage_marker} {det['object']} ({det['confidence']}% confidence)")
        
        # Show the frame
        cv2.imshow("Smart Campus - Object Detection Test", annotated_frame)
        
        # Check for quit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print(f"\n✅ Total frames processed: {frame_count}")
            break
    
    # Clean up
    cam.release()
    print("\n" + "="*60)
    print("OBJECT DETECTION TEST COMPLETED")
    print("="*60)


# If this file is run directly, test object detection
if __name__ == "__main__":
    test_object_detection()