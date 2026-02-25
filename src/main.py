# main.py
# Main application entry point for Smart Campus Monitoring System

import cv2
from camera_module import CameraModule
from object_detector import ObjectDetector
from dumping_detector import DumpingDetector
from evidence_manager import EvidenceManager
from cleanliness_monitor import CleanlinessMonitor
from alert_system import AlertSystem
from report_generator import ReportGenerator

def print_banner():
    """Print application banner"""
    print("\n" + "="*80)
    print(" "*15 + "SMART CAMPUS CLEANLINESS MONITORING SYSTEM")
    print(" "*20 + "AI-Based Illegal Dumping Detection")
    print("="*80)
    print("\n📋 System Features:")
    print("   ✓ Real-time AI object detection (YOLOv8)")
    print("   ✓ Intelligent illegal dumping detection")
    print("   ✓ Automatic image evidence capture")
    print("   ✓ Automatic video evidence recording (15-second clips)")
    print("   ✓ Live cleanliness scoring and monitoring")
    print("   ✓ Automated alert generation")
    print("   ✓ Professional report generation")
    print("\n" + "="*80 + "\n")

def main():
    """Main application function"""
    
    # Print banner
    print_banner()
    
    # Configuration
    LOCATION_NAME = "Main Campus - Monitoring Area"
    CAMERA_INDEX = 0
    DISTANCE_THRESHOLD = 150
    FRAMES_TO_CONFIRM = 30
    ENABLE_VIDEO_RECORDING = True  # Set to False to disable video
    VIDEO_BUFFER_SECONDS = 10      # Seconds of pre-dumping footage to capture
    
    print("🔧 Initializing all system components...\n")
    
    try:
        # Initialize all components
        cam = CameraModule(camera_index=CAMERA_INDEX)
        detector = ObjectDetector()
        dumping_detector = DumpingDetector(
            distance_threshold=DISTANCE_THRESHOLD, 
            frames_to_confirm=FRAMES_TO_CONFIRM
        )
        evidence_manager = EvidenceManager(
            evidence_folder='evidence',
            enable_video=ENABLE_VIDEO_RECORDING,
            buffer_seconds=VIDEO_BUFFER_SECONDS
        )
        cleanliness_monitor = CleanlinessMonitor(data_folder='data')
        alert_system = AlertSystem(alerts_folder='reports')
        report_generator = ReportGenerator(reports_folder='reports')
        
        print("\n" + "="*80)
        print("✅ ALL SYSTEMS INITIALIZED SUCCESSFULLY!")
        print("="*80)
        print(f"\n📍 Monitoring Location: {LOCATION_NAME}")
        print(f"📹 Camera: Active (Index {CAMERA_INDEX})")
        print(f"🤖 AI Model: YOLOv8 Nano (Loaded)")
        print(f"⚙️  Detection Threshold: {DISTANCE_THRESHOLD} pixels")
        print(f"⏱️  Confirmation Frames: {FRAMES_TO_CONFIRM}")
        print(f"📸 Image Evidence: Enabled")
        if ENABLE_VIDEO_RECORDING:
            print(f"🎬 Video Evidence: Enabled ({VIDEO_BUFFER_SECONDS}s buffer + 5s post-dump)")
        else:
            print(f"🎬 Video Evidence: Disabled")
        
        print("\n" + "="*80)
        print("🎥 STARTING LIVE MONITORING...")
        print("="*80)
        print("\n📖 Instructions:")
        print("   • The system is now monitoring for illegal dumping")
        print("   • All detections are logged automatically")
        print("   • Images + Videos saved when dumping detected")
        print("   • Press 'q' to stop monitoring and generate final report")
        print("   • Press 's' to take a manual screenshot")
        print("\n")
        
        # Tracking variables
        alert_display_timer = 0
        current_alert_text = ""
        show_alert_banner = False
        screenshot_count = 0
        
        # Main monitoring loop
        while True:
            # Read frame from camera
            success, frame = cam.read_frame()
            
            if not success:
                print("❌ Failed to read camera frame")
                break
            
            # Add frame to evidence buffer (for video recording)
            evidence_manager.add_frame_to_buffer(frame)
            
            # Detect objects using AI
            results, annotated_frame = detector.detect_objects(frame)
            detections = detector.extract_detections(results)
            
            # Analyze for illegal dumping
            analysis = dumping_detector.analyze_frame(detections, frame)
            
            # If dumping detected, take action
            if analysis['dumping_detected']:
                # Save evidence (image + start video recording)
                evidence_data = evidence_manager.save_evidence(
                    analysis['dumping_info'],
                    location_name=LOCATION_NAME
                )
                
                # Generate alert
                alert_data = alert_system.create_alert(
                    analysis['dumping_info'],
                    location_name=LOCATION_NAME,
                    evidence_path=evidence_data['image_path'] if evidence_data else None
                )
                
                # Show visual alert
                show_alert_banner = True
                alert_display_timer = 150  # Show for ~5 seconds
                current_alert_text = f"{alert_data['object']} - {alert_data['alert_id']}"
            
            # If currently recording video, add frames
            if evidence_manager.is_recording:
                video_complete = evidence_manager.add_frame_to_video(annotated_frame)
                
                # Show recording indicator on screen (red circle + "REC")
                cv2.circle(annotated_frame, (annotated_frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
                cv2.putText(annotated_frame, "REC", 
                           (annotated_frame.shape[1] - 70, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Show remaining frames count
                remaining_frames = evidence_manager.post_dump_duration - evidence_manager.post_dump_frames
                remaining_seconds = remaining_frames / 30.0
                cv2.putText(annotated_frame, f"{remaining_seconds:.1f}s", 
                           (annotated_frame.shape[1] - 70, 55),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Update cleanliness monitoring
            cleanliness_monitor.update_session(
                detections, 
                frame.shape, 
                dumping_detected=analysis['dumping_detected']
            )
            
            # Draw all visualizations
            final_frame = dumping_detector.draw_analysis(annotated_frame, detections, analysis)
            final_frame = cleanliness_monitor.draw_cleanliness_info(final_frame, detections)
            final_frame = alert_system.draw_alert_notification(
                final_frame, 
                show_alert=show_alert_banner,
                alert_text=current_alert_text
            )
            
            # Countdown alert display timer
            if alert_display_timer > 0:
                alert_display_timer -= 1
                if alert_display_timer == 0:
                    show_alert_banner = False
            
            # Add instructions overlay
            cv2.putText(final_frame, "Press 'q' to quit | Press 's' for screenshot", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Add evidence counter
            summary = evidence_manager.get_evidence_summary()
            evidence_text = f"Evidence: {summary['session_saves']} (Img: {summary['total_incidents']}, Vid: {summary['total_videos']})"
            cv2.putText(final_frame, evidence_text,
                       (10, final_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Display the frame
            cv2.imshow("Smart Campus Monitoring System", final_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n⏹️  Stopping monitoring...")
                break
            elif key == ord('s'):
                # Manual screenshot
                screenshot_count += 1
                screenshot_path = f"reports/screenshot_{screenshot_count}.jpg"
                cv2.imwrite(screenshot_path, final_frame)
                print(f"📸 Screenshot saved: {screenshot_path}")
        
        print("\n" + "="*80)
        print("FINALIZING SESSION...")
        print("="*80 + "\n")
        
        # Stop any ongoing video recording
        if evidence_manager.is_recording:
            print("⏹️  Stopping video recording...")
            evidence_manager.stop_video_recording()
        
        # Finalize session
        cleanliness_monitor.finalize_session(location_name=LOCATION_NAME)
        
        # Gather all data
        cleanliness_data = {
            'current_session': cleanliness_monitor.current_session,
            'history': cleanliness_monitor.history
        }
        evidence_data = evidence_manager.get_evidence_summary()
        alert_data = alert_system.get_session_summary()
        
        # Generate final report
        print("📊 Generating comprehensive session report...\n")
        report_path = report_generator.generate_report(
            cleanliness_data,
            evidence_data,
            alert_data,
            location_name=LOCATION_NAME
        )
        
        # Print final summaries
        print("\n" + "="*80)
        print("FINAL SESSION SUMMARY")
        print("="*80 + "\n")
        
        cleanliness_monitor.print_session_summary()
        
        print("📸 Evidence & Alerts:")
        print(f"   Evidence Files (Images): {evidence_data['total_incidents']}")
        print(f"   Evidence Files (Videos): {evidence_data['total_videos']}")
        print(f"   Alerts Generated: {alert_data['total_alerts']}")
        print(f"   Evidence Folder: {evidence_data['evidence_folder']}")
        print(f"   Alerts Folder: {alert_data['alerts_folder']}")
        
        if report_path:
            print(f"\n📄 Final Report: {report_path}")
        
        print("\n" + "="*80)
        print("✅ SESSION COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\n💡 You can now:")
        print("   • Review saved evidence images in 'evidence/' folder")
        print("   • Watch saved video clips in 'evidence/' folder")
        print("   • Read alert files in 'reports/' folder")
        print("   • Open the final report for complete analysis")
        print("\n" + "="*80 + "\n")
        
        # Cleanup
        cam.release()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        # Stop any ongoing video recording
        if 'evidence_manager' in locals() and evidence_manager.is_recording:
            evidence_manager.stop_video_recording()
        if 'cam' in locals():
            cam.release()
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Please check your camera connection and try again.")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if 'evidence_manager' in locals() and evidence_manager.is_recording:
            evidence_manager.stop_video_recording()
        if 'cam' in locals():
            cam.release()

if __name__ == "__main__":
    main()