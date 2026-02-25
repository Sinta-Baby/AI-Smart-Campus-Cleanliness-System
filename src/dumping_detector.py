# dumping_detector.py
# This module detects illegal dumping by analyzing object positions and person movements

import cv2
import numpy as np
from datetime import datetime
import os

class DumpingDetector:
    """
    A class to detect illegal dumping activities
    """
    
    def __init__(self, distance_threshold=150, frames_to_confirm=30):
        """
        Initialize the dumping detector
        
        Args:
            distance_threshold: Max distance (pixels) between person and garbage to consider "carrying"
            frames_to_confirm: How many frames garbage must persist without person to confirm dumping
        """
        print("🧠 Initializing Dumping Detector...")
        
        self.distance_threshold = distance_threshold
        self.frames_to_confirm = frames_to_confirm
        
        # Track garbage objects over time
        self.tracked_garbage = {}  # Format: {garbage_id: {info}}
        
        # Counter for generating unique IDs
        self.next_id = 1
        
        # List to store confirmed dumping events
        self.dumping_events = []
        
        print("✅ Dumping Detector initialized!")
        print(f"   Distance threshold: {distance_threshold} pixels")
        print(f"   Confirmation frames: {frames_to_confirm}")
    
    def calculate_distance(self, box1, box2):
        """
        Calculate distance between centers of two boxes
        
        Args:
            box1: [x1, y1, x2, y2]
            box2: [x1, y1, x2, y2]
            
        Returns:
            distance: Distance in pixels
        """
        # Calculate center points
        center1_x = (box1[0] + box1[2]) / 2
        center1_y = (box1[1] + box1[3]) / 2
        
        center2_x = (box2[0] + box2[2]) / 2
        center2_y = (box2[1] + box2[3]) / 2
        
        # Euclidean distance formula: sqrt((x2-x1)² + (y2-y1)²)
        distance = np.sqrt((center2_x - center1_x)**2 + (center2_y - center1_y)**2)
        
        return distance
    
    def find_nearest_person(self, garbage_box, person_boxes):
        """
        Find the closest person to a garbage object
        
        Args:
            garbage_box: Box coordinates of garbage
            person_boxes: List of box coordinates of all persons
            
        Returns:
            min_distance: Distance to nearest person (or None if no persons)
            nearest_person_box: Box of nearest person (or None)
        """
        if len(person_boxes) == 0:
            return None, None
        
        min_distance = float('inf')
        nearest_person_box = None
        
        for person_box in person_boxes:
            distance = self.calculate_distance(garbage_box, person_box)
            
            if distance < min_distance:
                min_distance = distance
                nearest_person_box = person_box
        
        return min_distance, nearest_person_box
    
    def analyze_frame(self, detections, frame):
        """
        Analyze detections to identify illegal dumping
        
        Args:
            detections: List of detected objects from object_detector
            frame: Current video frame
            
        Returns:
            analysis_result: Dictionary containing analysis info
        """
        # Separate persons and garbage from detections
        person_boxes = []
        garbage_items = []
        
        for det in detections:
            if det['object'] == 'person':
                person_boxes.append(det['box'])
            elif det['is_garbage']:
                garbage_items.append(det)
        
        # Result dictionary
        result = {
            'persons_count': len(person_boxes),
            'garbage_count': len(garbage_items),
            'dumping_detected': False,
            'dumping_info': None
        }
        
        # If no garbage detected, clear all tracking
        if len(garbage_items) == 0:
            self.tracked_garbage = {}
            return result
        
        # Analyze each garbage item
        current_garbage_ids = []
        
        for garbage in garbage_items:
            garbage_box = garbage['box']
            
            # Find nearest person
            min_distance, nearest_person = self.find_nearest_person(garbage_box, person_boxes)
            
            # Check if this garbage is close to any person
            is_with_person = (min_distance is not None and min_distance < self.distance_threshold)
            
            # Try to match with existing tracked garbage (simple position matching)
            matched_id = None
            for tracked_id, tracked_info in self.tracked_garbage.items():
                tracked_box = tracked_info['last_box']
                distance_to_tracked = self.calculate_distance(garbage_box, tracked_box)
                
                # If within 50 pixels, consider it the same object
                if distance_to_tracked < 50:
                    matched_id = tracked_id
                    break
            
            # If matched with existing tracked garbage
            if matched_id is not None:
                # Update tracking info
                self.tracked_garbage[matched_id]['last_box'] = garbage_box
                self.tracked_garbage[matched_id]['last_seen_frame'] += 1
                
                if is_with_person:
                    # Reset counter if person is near
                    self.tracked_garbage[matched_id]['frames_without_person'] = 0
                else:
                    # Increment counter if no person nearby
                    self.tracked_garbage[matched_id]['frames_without_person'] += 1
                
                # Check if dumping is confirmed
                if self.tracked_garbage[matched_id]['frames_without_person'] >= self.frames_to_confirm:
                    if not self.tracked_garbage[matched_id]['dumping_confirmed']:
                        # DUMPING DETECTED!
                        self.tracked_garbage[matched_id]['dumping_confirmed'] = True
                        
                        # Create dumping event
                        dumping_event = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'object': garbage['object'],
                            'confidence': garbage['confidence'],
                            'location': garbage_box,
                            'frame': frame.copy()
                        }
                        
                        self.dumping_events.append(dumping_event)
                        
                        result['dumping_detected'] = True
                        result['dumping_info'] = dumping_event
                        
                        print("\n" + "="*60)
                        print("🚨 ILLEGAL DUMPING DETECTED!")
                        print(f"   Object: {garbage['object']}")
                        print(f"   Confidence: {garbage['confidence']}%")
                        print(f"   Time: {dumping_event['timestamp']}")
                        print("="*60 + "\n")
                
                current_garbage_ids.append(matched_id)
            
            else:
                # New garbage object - start tracking
                new_id = self.next_id
                self.next_id += 1
                
                self.tracked_garbage[new_id] = {
                    'object': garbage['object'],
                    'first_box': garbage_box,
                    'last_box': garbage_box,
                    'last_seen_frame': 1,
                    'frames_without_person': 0 if is_with_person else 1,
                    'dumping_confirmed': False
                }
                
                current_garbage_ids.append(new_id)
        
        # Remove garbage that's no longer visible
        ids_to_remove = [gid for gid in self.tracked_garbage.keys() if gid not in current_garbage_ids]
        for gid in ids_to_remove:
            del self.tracked_garbage[gid]
        
        return result
    
    def draw_analysis(self, frame, detections, analysis_result):
        """
        Draw analysis information on frame
        
        Args:
            frame: Video frame to draw on
            detections: List of detections
            analysis_result: Result from analyze_frame
            
        Returns:
            annotated_frame: Frame with drawings
        """
        annotated_frame = frame.copy()
        
        # Draw status info
        status_text = f"Persons: {analysis_result['persons_count']} | Garbage: {analysis_result['garbage_count']}"
        cv2.putText(annotated_frame, status_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw tracked garbage info
        cv2.putText(annotated_frame, f"Tracking: {len(self.tracked_garbage)} objects", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # If dumping detected, show alert
        if analysis_result['dumping_detected']:
            # Draw red warning box
            cv2.rectangle(annotated_frame, (5, 5), (635, 90), (0, 0, 255), 3)
            cv2.putText(annotated_frame, "DUMPING DETECTED!", (150, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        # Draw circles around tracked garbage
        for gid, info in self.tracked_garbage.items():
            box = info['last_box']
            center_x = int((box[0] + box[2]) / 2)
            center_y = int((box[1] + box[3]) / 2)
            
            # Color based on status
            if info['dumping_confirmed']:
                color = (0, 0, 255)  # Red = confirmed dumping
            elif info['frames_without_person'] > 0:
                color = (0, 165, 255)  # Orange = suspicious
            else:
                color = (0, 255, 0)  # Green = with person
            
            cv2.circle(annotated_frame, (center_x, center_y), 30, color, 3)
            
            # Show frame count
            cv2.putText(annotated_frame, str(info['frames_without_person']),
                       (center_x - 10, center_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, color, 2)
        
        return annotated_frame


def test_dumping_detection():
    """
    Test the complete system: Camera + Object Detection + Dumping Detection
    """
    print("\n" + "="*60)
    print("TESTING COMPLETE ILLEGAL DUMPING DETECTION SYSTEM")
    print("="*60 + "\n")
    
    # Import required modules
    from camera_module import CameraModule
    from object_detector import ObjectDetector
    
    # Initialize all components
    cam = CameraModule(camera_index=0)
    detector = ObjectDetector()
    dumping_detector = DumpingDetector(distance_threshold=150, frames_to_confirm=30)
    
    print("\n🎥 Starting live dumping detection...")
    print("👉 TEST INSTRUCTIONS:")
    print("   1. Hold a bottle/cup close to your face (AI sees person + garbage together)")
    print("   2. Place the bottle/cup on table and move away from camera")
    print("   3. Stay away for ~2-3 seconds")
    print("   4. System should detect ILLEGAL DUMPING!")
    print("\nPress 'q' to quit\n")
    
    frame_count = 0
    
    while True:
        # Read frame
        success, frame = cam.read_frame()
        
        if not success:
            break
        
        frame_count += 1
        
        # Detect objects
        results, annotated_frame = detector.detect_objects(frame)
        detections = detector.extract_detections(results)
        
        # Analyze for dumping
        analysis = dumping_detector.analyze_frame(detections, frame)
        
        # Draw analysis on frame
        final_frame = dumping_detector.draw_analysis(annotated_frame, detections, analysis)
        
        # Add instructions
        cv2.putText(final_frame, "Press 'q' to quit", (10, 470),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("Smart Campus - Dumping Detection", final_frame)
        
        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Show summary
    print("\n" + "="*60)
    print("DETECTION SUMMARY")
    print("="*60)
    print(f"Total frames processed: {frame_count}")
    print(f"Total dumping events detected: {len(dumping_detector.dumping_events)}")
    
    if len(dumping_detector.dumping_events) > 0:
        print("\n📋 Dumping Events:")
        for i, event in enumerate(dumping_detector.dumping_events, 1):
            print(f"   {i}. {event['object']} at {event['timestamp']}")
    
    print("="*60 + "\n")
    
    # Clean up
    cam.release()


# If this file is run directly, test dumping detection
if __name__ == "__main__":
    test_dumping_detection()