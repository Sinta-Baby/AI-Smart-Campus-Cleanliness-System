# cleanliness_monitor.py
# This module monitors and tracks cleanliness levels over time

import cv2
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class CleanlinessMonitor:
    """
    A class to monitor and track area cleanliness
    """
    
    def __init__(self, data_folder='data'):
        """
        Initialize the cleanliness monitor
        
        Args:
            data_folder: Folder to store cleanliness data
        """
        print("📊 Initializing Cleanliness Monitor...")
        
        self.data_folder = data_folder
        
        # Create data folder if it doesn't exist
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
            print(f"   ✅ Created data folder: {data_folder}")
        
        # File to store cleanliness history
        self.history_file = os.path.join(data_folder, 'cleanliness_history.json')
        
        # Load existing history or create new
        self.history = self.load_history()
        
        # Current session data
        self.current_session = {
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'frames_analyzed': 0,
            'garbage_detections': 0,
            'dumping_events': 0,
            'cleanliness_samples': []
        }
        
        print("✅ Cleanliness Monitor ready!")
    
    def load_history(self):
        """
        Load cleanliness history from file
        
        Returns:
            history: Dictionary with historical data
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                print(f"   📂 Loaded history: {len(history.get('sessions', []))} previous sessions")
                return history
            except:
                print("   ⚠️ Could not load history, starting fresh")
                return {'sessions': []}
        else:
            print("   📝 No history found, starting fresh")
            return {'sessions': []}
    
    def save_history(self):
        """
        Save cleanliness history to file
        """
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
            print(f"   💾 History saved to {self.history_file}")
        except Exception as e:
            print(f"   ❌ Error saving history: {e}")
    
    def calculate_cleanliness_score(self, detections, frame_shape):
        """
        Calculate cleanliness score for current frame
        
        Args:
            detections: List of detected objects
            frame_shape: Shape of the frame (height, width, channels)
            
        Returns:
            score: Cleanliness score (0-100)
            rating: Text rating (Excellent/Good/Fair/Poor)
            garbage_count: Number of garbage objects detected
            color: Color for rating display
        """
        # Count garbage objects
        garbage_objects = [d for d in detections if d.get('is_garbage', False)]
        garbage_count = len(garbage_objects)
        
        # Calculate total garbage area (sum of bounding box areas)
        total_frame_area = frame_shape[0] * frame_shape[1]  # height × width
        garbage_area = 0
        
        for obj in garbage_objects:
            box = obj['box']
            width = box[2] - box[0]
            height = box[3] - box[1]
            garbage_area += width * height
        
        # Calculate garbage coverage percentage
        garbage_percentage = (garbage_area / total_frame_area) * 100
        
        # Calculate cleanliness score (inverse of garbage coverage)
        # Also penalize by number of items
        item_penalty = min(garbage_count * 2, 30)  # Max 30% penalty for items
        cleanliness_score = max(0, 100 - garbage_percentage - item_penalty)
        
        # Determine rating
        if cleanliness_score >= 90:
            rating = "Excellent"
            color = (0, 255, 0)  # Green
        elif cleanliness_score >= 70:
            rating = "Good"
            color = (0, 255, 255)  # Yellow
        elif cleanliness_score >= 50:
            rating = "Fair"
            color = (0, 165, 255)  # Orange
        else:
            rating = "Poor"
            color = (0, 0, 255)  # Red
        
        return cleanliness_score, rating, garbage_count, color
    
    def update_session(self, detections, frame_shape, dumping_detected=False):
        """
        Update current session statistics
        
        Args:
            detections: List of detected objects
            frame_shape: Shape of the frame
            dumping_detected: Whether dumping was detected this frame
        """
        self.current_session['frames_analyzed'] += 1
        
        # Count garbage
        garbage_count = len([d for d in detections if d.get('is_garbage', False)])
        self.current_session['garbage_detections'] += garbage_count
        
        if dumping_detected:
            self.current_session['dumping_events'] += 1
        
        # Calculate and store cleanliness score (sample every 30 frames)
        if self.current_session['frames_analyzed'] % 30 == 0:
            score, rating, _, _ = self.calculate_cleanliness_score(detections, frame_shape)
            
            sample = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'score': round(score, 2),
                'rating': rating,
                'garbage_count': garbage_count
            }
            
            self.current_session['cleanliness_samples'].append(sample)
    
    def get_session_average(self):
        """
        Calculate average cleanliness score for current session
        
        Returns:
            average_score: Average cleanliness score
            average_rating: Rating based on average
        """
        if len(self.current_session['cleanliness_samples']) == 0:
            return 100, "Excellent"
        
        scores = [s['score'] for s in self.current_session['cleanliness_samples']]
        average_score = sum(scores) / len(scores)
        
        # Determine rating
        if average_score >= 90:
            average_rating = "Excellent"
        elif average_score >= 70:
            average_rating = "Good"
        elif average_score >= 50:
            average_rating = "Fair"
        else:
            average_rating = "Poor"
        
        return round(average_score, 2), average_rating
    
    def finalize_session(self, location_name="Campus Area"):
        """
        Save current session to history
        
        Args:
            location_name: Name of monitored location
        """
        avg_score, avg_rating = self.get_session_average()
        
        session_summary = {
            'location': location_name,
            'start_time': self.current_session['start_time'],
            'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'frames_analyzed': self.current_session['frames_analyzed'],
            'total_garbage_detections': self.current_session['garbage_detections'],
            'dumping_events': self.current_session['dumping_events'],
            'average_cleanliness_score': avg_score,
            'rating': avg_rating,
            'samples': self.current_session['cleanliness_samples']
        }
        
        self.history['sessions'].append(session_summary)
        self.save_history()
        
        return session_summary
    
    def draw_cleanliness_info(self, frame, detections):
        """
        Draw cleanliness information on frame
        
        Args:
            frame: Video frame to draw on
            detections: List of detected objects
            
        Returns:
            annotated_frame: Frame with cleanliness info
        """
        annotated_frame = frame.copy()
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate current cleanliness
        score, rating, garbage_count, color = self.calculate_cleanliness_score(
            detections, frame.shape
        )
        
        # Draw cleanliness panel (right side)
        panel_width = 250
        panel_x = frame_width - panel_width - 10
        panel_y = 10
        
        # Semi-transparent background
        overlay = annotated_frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), 
                     (frame_width - 10, panel_y + 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
        
        # Add border
        cv2.rectangle(annotated_frame, (panel_x, panel_y), 
                     (frame_width - 10, panel_y + 150), color, 2)
        
        # Title
        cv2.putText(annotated_frame, "CLEANLINESS MONITOR", 
                   (panel_x + 10, panel_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Score (large)
        cv2.putText(annotated_frame, f"{int(score)}%", 
                   (panel_x + 70, panel_y + 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 4)
        
        # Rating
        cv2.putText(annotated_frame, rating, 
                   (panel_x + 80, panel_y + 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Garbage count
        cv2.putText(annotated_frame, f"Garbage: {garbage_count}", 
                   (panel_x + 10, panel_y + 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Session stats (bottom left)
        avg_score, avg_rating = self.get_session_average()
        stats_text = [
            f"Session Average: {avg_score}% ({avg_rating})",
            f"Frames: {self.current_session['frames_analyzed']}",
            f"Dumping Events: {self.current_session['dumping_events']}"
        ]
        
        y_offset = frame_height - 90
        for i, text in enumerate(stats_text):
            cv2.putText(annotated_frame, text, (10, y_offset + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated_frame
    
    def print_session_summary(self):
        """
        Print detailed session summary
        """
        print("\n" + "="*70)
        print("CLEANLINESS MONITORING SESSION SUMMARY")
        print("="*70)
        
        avg_score, avg_rating = self.get_session_average()
        
        print(f"\n📊 Session Statistics:")
        print(f"   Start Time: {self.current_session['start_time']}")
        print(f"   Frames Analyzed: {self.current_session['frames_analyzed']}")
        print(f"   Total Garbage Detections: {self.current_session['garbage_detections']}")
        print(f"   Dumping Events: {self.current_session['dumping_events']}")
        
        print(f"\n🎯 Cleanliness Score:")
        print(f"   Average Score: {avg_score}%")
        print(f"   Rating: {avg_rating}")
        
        if len(self.current_session['cleanliness_samples']) > 0:
            scores = [s['score'] for s in self.current_session['cleanliness_samples']]
            print(f"   Highest: {max(scores)}%")
            print(f"   Lowest: {min(scores)}%")
        
        print("\n" + "="*70 + "\n")


def test_cleanliness_monitor():
    """
    Test complete system with cleanliness monitoring
    """
    print("\n" + "="*70)
    print("TESTING COMPLETE SYSTEM WITH CLEANLINESS MONITORING")
    print("="*70 + "\n")
    
    from camera_module import CameraModule
    from object_detector import ObjectDetector
    from dumping_detector import DumpingDetector
    from evidence_manager import EvidenceManager
    
    # Initialize all components
    cam = CameraModule(camera_index=0)
    detector = ObjectDetector()
    dumping_detector = DumpingDetector(distance_threshold=150, frames_to_confirm=30)
    evidence_manager = EvidenceManager(evidence_folder='evidence')
    cleanliness_monitor = CleanlinessMonitor(data_folder='data')
    
    print("\n🎥 Starting complete monitoring system...")
    print("👉 The system now tracks:")
    print("   • Object detection")
    print("   • Illegal dumping")
    print("   • Evidence capture")
    print("   • Cleanliness levels")
    print("\nPress 'q' to quit\n")
    
    while True:
        success, frame = cam.read_frame()
        
        if not success:
            break
        
        # Detect objects
        results, annotated_frame = detector.detect_objects(frame)
        detections = detector.extract_detections(results)
        
        # Analyze for dumping
        analysis = dumping_detector.analyze_frame(detections, frame)
        
        # Save evidence if dumping detected
        if analysis['dumping_detected']:
            evidence_manager.save_evidence(
                analysis['dumping_info'],
                location_name="Main Campus - Test Area"
            )
        
        # Update cleanliness monitoring
        cleanliness_monitor.update_session(
            detections, 
            frame.shape, 
            dumping_detected=analysis['dumping_detected']
        )
        
        # Draw analysis
        final_frame = dumping_detector.draw_analysis(annotated_frame, detections, analysis)
        
        # Draw cleanliness info
        final_frame = cleanliness_monitor.draw_cleanliness_info(final_frame, detections)
        
        # Add quit instruction
        cv2.putText(final_frame, "Press 'q' to quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("Smart Campus - Complete System", final_frame)
        
        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Finalize and save session
    session_summary = cleanliness_monitor.finalize_session(
        location_name="Main Campus - Test Area"
    )
    
    # Print summaries
    cleanliness_monitor.print_session_summary()
    
    evidence_summary = evidence_manager.get_evidence_summary()
    print("📸 Evidence Summary:")
    print(f"   Total incidents saved: {evidence_summary['total_incidents']}")
    print(f"   Evidence folder: {evidence_summary['evidence_folder']}")
    print(f"   Log file: {evidence_summary['log_file']}")
    
    print("\n✅ All systems tested successfully!")
    
    # Clean up
    cam.release()


# If this file is run directly, test cleanliness monitor
if __name__ == "__main__":
    test_cleanliness_monitor()