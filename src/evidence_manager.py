# evidence_manager.py
# This module handles saving evidence (images, videos, and logs) when dumping is detected

import cv2
import os
from datetime import datetime
import json
from collections import deque

class EvidenceManager:
    """
    A class to manage evidence storage (images and videos)
    """
    
    def __init__(self, evidence_folder='evidence', enable_video=True, buffer_seconds=10):
        """
        Initialize the evidence manager
        
        Args:
            evidence_folder: Path to folder where evidence will be saved
            enable_video: Whether to record video evidence
            buffer_seconds: How many seconds of video to keep before dumping (buffer)
        """
        print("💾 Initializing Evidence Manager...")
        
        self.evidence_folder = evidence_folder
        self.enable_video = enable_video
        self.buffer_seconds = buffer_seconds
        
        # Create evidence folder if it doesn't exist
        if not os.path.exists(evidence_folder):
            os.makedirs(evidence_folder)
            print(f"   ✅ Created evidence folder: {evidence_folder}")
        else:
            print(f"   ✅ Using existing folder: {evidence_folder}")
        
        # Path to log file
        self.log_file = os.path.join(evidence_folder, 'dumping_log.txt')
        
        # Initialize log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("="*70 + "\n")
                f.write("SMART CAMPUS ILLEGAL DUMPING LOG\n")
                f.write("="*70 + "\n\n")
            print(f"   ✅ Created log file: {self.log_file}")
        
        # Counter for evidence saved
        self.evidence_count = 0
        
        # Video recording setup
        if self.enable_video:
            # Frame buffer to store recent frames (for pre-dumping footage)
            # 30 FPS × buffer_seconds = number of frames to store
            self.frame_buffer = deque(maxlen=30 * buffer_seconds)
            self.is_recording = False
            self.video_writer = None
            self.post_dump_frames = 0
            self.post_dump_duration = 5 * 30  # 5 seconds × 30 FPS = 150 frames
            self.current_video_path = None
            print(f"   ✅ Video recording enabled (buffer: {buffer_seconds}s)")
        
        print("✅ Evidence Manager ready!")
    
    def add_frame_to_buffer(self, frame):
        """
        Add frame to circular buffer (for pre-dumping footage)
        
        Args:
            frame: Video frame to buffer
        """
        if self.enable_video:
            self.frame_buffer.append(frame.copy())
    
    def start_video_recording(self, dumping_info):
        """
        Start recording video when dumping is detected
        
        Args:
            dumping_info: Dictionary with dumping details
            
        Returns:
            video_path: Path where video will be saved
        """
        if not self.enable_video:
            return None
        
        # Generate video filename
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        object_name = dumping_info['object'].replace(" ", "_")
        video_filename = f"{timestamp_str}_{object_name}.avi"
        self.current_video_path = os.path.join(self.evidence_folder, video_filename)
        
        # Get frame dimensions from buffer
        if len(self.frame_buffer) > 0:
            frame_height, frame_width = self.frame_buffer[0].shape[:2]
            
            # Define video codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # XVID codec for .avi
            self.video_writer = cv2.VideoWriter(
                self.current_video_path,
                fourcc,
                30.0,  # FPS
                (frame_width, frame_height)
            )
            
            # Write buffered frames (pre-dumping footage)
            print(f"\n🎬 Starting video recording: {video_filename}")
            print(f"   Writing {len(self.frame_buffer)} buffered frames...")
            
            for buffered_frame in self.frame_buffer:
                self.video_writer.write(buffered_frame)
            
            self.is_recording = True
            self.post_dump_frames = 0
            
            return self.current_video_path
        
        return None
    
    def add_frame_to_video(self, frame):
        """
        Add frame to ongoing video recording
        
        Args:
            frame: Video frame to add
            
        Returns:
            video_complete: True if video recording is finished
        """
        if not self.enable_video or not self.is_recording:
            return False
        
        # Write frame to video
        if self.video_writer is not None:
            self.video_writer.write(frame)
            self.post_dump_frames += 1
            
            # Check if we've recorded enough post-dump frames
            if self.post_dump_frames >= self.post_dump_duration:
                return self.stop_video_recording()
        
        return False
    
    def stop_video_recording(self):
        """
        Stop and finalize video recording
        
        Returns:
            video_path: Path to saved video
        """
        if not self.enable_video or not self.is_recording:
            return None
        
        print(f"   ✅ Video recording complete: {self.current_video_path}")
        
        # Release video writer
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        
        self.is_recording = False
        video_path = self.current_video_path
        self.current_video_path = None
        
        return video_path
    
    def add_annotations_to_frame(self, frame, dumping_info, location_name="Campus Area"):
        """
        Add informational text overlay to the evidence frame
        
        Args:
            frame: The image frame to annotate
            dumping_info: Dictionary with dumping details
            location_name: Name of the location (for future use)
            
        Returns:
            annotated_frame: Frame with annotations added
        """
        annotated_frame = frame.copy()
        
        # Add semi-transparent overlay at top for text background
        overlay = annotated_frame.copy()
        cv2.rectangle(overlay, (0, 0), (annotated_frame.shape[1], 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated_frame, 0.4, 0, annotated_frame)
        
        # Add header text
        cv2.putText(annotated_frame, "ILLEGAL DUMPING EVIDENCE", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
        
        # Add timestamp
        cv2.putText(annotated_frame, f"Time: {dumping_info['timestamp']}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add object info
        object_text = f"Object: {dumping_info['object']} ({dumping_info['confidence']}%)"
        cv2.putText(annotated_frame, object_text, 
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add location
        cv2.putText(annotated_frame, f"Location: {location_name}", 
                    (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def save_evidence(self, dumping_info, location_name="Campus Area"):
        """
        Save evidence image and start video recording
        
        Args:
            dumping_info: Dictionary containing dumping details
            location_name: Location where dumping occurred
            
        Returns:
            evidence_data: Dictionary with paths to saved files
        """
        try:
            # Generate filename with timestamp and object type
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            object_name = dumping_info['object'].replace(" ", "_")
            
            # Save image evidence
            image_filename = f"{timestamp_str}_{object_name}.jpg"
            image_filepath = os.path.join(self.evidence_folder, image_filename)
            
            # Get frame and add annotations
            frame = dumping_info['frame']
            annotated_frame = self.add_annotations_to_frame(frame, dumping_info, location_name)
            
            # Save image
            cv2.imwrite(image_filepath, annotated_frame)
            
            # Start video recording
            video_filepath = None
            if self.enable_video:
                video_filepath = self.start_video_recording(dumping_info)
            
            # Log the incident
            self.log_incident(dumping_info, image_filename, location_name, video_filepath)
            
            # Increment counter
            self.evidence_count += 1
            
            print(f"\n📸 Evidence saved: {image_filename}")
            print(f"   Image: {image_filepath}")
            if video_filepath:
                print(f"   Video: Recording started (will save {self.post_dump_duration/30:.0f}s of footage)")
            
            return {
                'image_path': image_filepath,
                'video_path': video_filepath,
                'timestamp': dumping_info['timestamp']
            }
            
        except Exception as e:
            print(f"❌ Error saving evidence: {e}")
            return None
    
    def log_incident(self, dumping_info, image_filename, location_name, video_filename=None):
        """
        Write incident details to log file
        
        Args:
            dumping_info: Dictionary with dumping details
            image_filename: Name of saved image file
            location_name: Location of incident
            video_filename: Name of saved video file (optional)
        """
        try:
            with open(self.log_file, 'a') as f:
                f.write("-" * 70 + "\n")
                f.write(f"Incident #{self.evidence_count + 1}\n")
                f.write(f"Timestamp: {dumping_info['timestamp']}\n")
                f.write(f"Location: {location_name}\n")
                f.write(f"Object Detected: {dumping_info['object']}\n")
                f.write(f"AI Confidence: {dumping_info['confidence']}%\n")
                f.write(f"Evidence Image: {image_filename}\n")
                if video_filename:
                    f.write(f"Evidence Video: {os.path.basename(video_filename)}\n")
                f.write("-" * 70 + "\n\n")
            
            print(f"   ✅ Incident logged to {self.log_file}")
            
        except Exception as e:
            print(f"   ❌ Error writing to log: {e}")
    
    def get_evidence_summary(self):
        """
        Get summary of all saved evidence
        
        Returns:
            summary: Dictionary with statistics
        """
        # Count image files in evidence folder
        image_files = [f for f in os.listdir(self.evidence_folder) 
                      if f.endswith('.jpg') or f.endswith('.png')]
        
        # Count video files
        video_files = [f for f in os.listdir(self.evidence_folder)
                      if f.endswith('.avi') or f.endswith('.mp4')]
        
        summary = {
            'total_incidents': len(image_files),
            'total_videos': len(video_files),
            'evidence_folder': self.evidence_folder,
            'log_file': self.log_file,
            'session_saves': self.evidence_count,
            'video_enabled': self.enable_video
        }
        
        return summary
    
    def display_recent_evidence(self, num_images=3):
        """
        Display most recent evidence images
        
        Args:
            num_images: Number of recent images to show
        """
        # Get all image files sorted by modification time
        image_files = [f for f in os.listdir(self.evidence_folder) 
                      if f.endswith('.jpg') or f.endswith('.png')]
        
        if len(image_files) == 0:
            print("📭 No evidence images found.")
            return
        
        # Sort by modification time (newest first)
        image_files.sort(key=lambda x: os.path.getmtime(
            os.path.join(self.evidence_folder, x)), reverse=True)
        
        # Show up to num_images
        for i, img_file in enumerate(image_files[:num_images]):
            img_path = os.path.join(self.evidence_folder, img_file)
            img = cv2.imread(img_path)
            
            if img is not None:
                cv2.imshow(f"Evidence #{i+1}: {img_file}", img)
        
        print(f"\n👁️ Displaying {min(num_images, len(image_files))} recent evidence images")
        print("Press any key to close windows...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def test_evidence_manager():
    """
    Test the evidence manager with video recording
    """
    print("\n" + "="*60)
    print("TESTING EVIDENCE MANAGER WITH VIDEO RECORDING")
    print("="*60 + "\n")
    
    from camera_module import CameraModule
    from object_detector import ObjectDetector
    from dumping_detector import DumpingDetector
    
    # Initialize all components
    cam = CameraModule(camera_index=0)
    detector = ObjectDetector()
    dumping_detector = DumpingDetector(distance_threshold=150, frames_to_confirm=30)
    evidence_manager = EvidenceManager(evidence_folder='evidence', enable_video=True, buffer_seconds=10)
    
    print("\n🎥 Starting system with IMAGE + VIDEO evidence capture...")
    print("👉 TEST INSTRUCTIONS:")
    print("   1. Hold object near your face")
    print("   2. Place it down and move away")
    print("   3. Wait for DUMPING DETECTED alert")
    print("   4. System will save IMAGE + record VIDEO!")
    print("   5. Video continues for 5 seconds after detection")
    print("\nPress 'q' to quit\n")
    
    frame_count = 0
    
    while True:
        success, frame = cam.read_frame()
        
        if not success:
            break
        
        frame_count += 1
        
        # Add frame to buffer (for pre-dumping video footage)
        evidence_manager.add_frame_to_buffer(frame)
        
        # Detect objects
        results, annotated_frame = detector.detect_objects(frame)
        detections = detector.extract_detections(results)
        
        # Analyze for dumping
        analysis = dumping_detector.analyze_frame(detections, frame)
        
        # If dumping detected, save evidence (image + start video)
        if analysis['dumping_detected']:
            evidence_data = evidence_manager.save_evidence(
                analysis['dumping_info'], 
                location_name="Test Camera - Main Campus"
            )
        
        # If currently recording video, add frames
        if evidence_manager.is_recording:
            video_complete = evidence_manager.add_frame_to_video(annotated_frame)
            
            # Show recording indicator
            cv2.circle(annotated_frame, (annotated_frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(annotated_frame, "REC", 
                       (annotated_frame.shape[1] - 70, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw analysis
        final_frame = dumping_detector.draw_analysis(annotated_frame, detections, analysis)
        
        # Add evidence count to display
        summary = evidence_manager.get_evidence_summary()
        cv2.putText(final_frame, f"Evidence: {summary['session_saves']} (Images: {summary['total_incidents']}, Videos: {summary['total_videos']})", 
                   (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.putText(final_frame, "Press 'q' to quit", 
                   (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("Smart Campus - Evidence Recording (Image + Video)", final_frame)
        
        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Stop any ongoing video recording
    if evidence_manager.is_recording:
        evidence_manager.stop_video_recording()
    
    # Show final summary
    print("\n" + "="*60)
    print("SESSION SUMMARY")
    print("="*60)
    summary = evidence_manager.get_evidence_summary()
    print(f"📊 Total incidents (all time): {summary['total_incidents']}")
    print(f"📸 Images saved this session: {summary['session_saves']}")
    print(f"🎬 Videos saved: {summary['total_videos']}")
    print(f"📁 Evidence folder: {summary['evidence_folder']}")
    print(f"📄 Log file: {summary['log_file']}")
    print("="*60 + "\n")
    
    # Ask if user wants to view evidence
    print("Would you like to view recent evidence? (Close camera window first)")
    
    cam.release()
    
    # Show recent evidence
    if summary['total_incidents'] > 0:
        print("\nDisplaying recent evidence images...")
        evidence_manager.display_recent_evidence(num_images=3)
    
    print("\n✅ Test complete!")


# If this file is run directly, test evidence manager
if __name__ == "__main__":
    test_evidence_manager()