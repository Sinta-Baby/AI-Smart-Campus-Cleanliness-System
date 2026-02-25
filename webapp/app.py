# webapp/app.py
# Flask web application for Smart Campus Monitoring System

from flask import Flask, render_template, jsonify, Response, send_from_directory, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import sys
import os
import json
import base64
from datetime import datetime
from threading import Thread, Lock
import time

# Add parent directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.camera_module import CameraModule
from src.object_detector import ObjectDetector
from src.dumping_detector import DumpingDetector
from src.evidence_manager import EvidenceManager
from src.cleanliness_monitor import CleanlinessMonitor
from src.alert_system import AlertSystem
from src.report_generator import ReportGenerator

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-campus-monitoring-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
monitoring_active = False
monitoring_thread = None
thread_lock = Lock()

# System components
camera = None
detector = None
dumping_detector = None
evidence_manager = None
cleanliness_monitor = None
alert_system = None

# Statistics
current_stats = {
    'cleanliness_score': 100,
    'rating': 'Excellent',
    'garbage_count': 0,
    'persons_count': 0,
    'total_incidents': 0,
    'total_alerts': 0,
    'monitoring_time': 0,
    'is_recording': False
}

def initialize_system():
    """Initialize all monitoring components"""
    global camera, detector, dumping_detector, evidence_manager
    global cleanliness_monitor, alert_system
    
    try:
        print("🔧 Initializing monitoring system...")
        
        camera = CameraModule(camera_index=0)
        detector = ObjectDetector()
        dumping_detector = DumpingDetector(distance_threshold=150, frames_to_confirm=30)
        evidence_manager = EvidenceManager(
            evidence_folder='evidence',
            enable_video=True,
            buffer_seconds=10
        )
        cleanliness_monitor = CleanlinessMonitor(data_folder='data')
        alert_system = AlertSystem(
            alerts_folder='reports',
            config_file='data/email_config.json'
        )
        
        print("✅ System initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        return False

def monitoring_loop():
    """Main monitoring loop running in background thread"""
    global monitoring_active, current_stats
    
    start_time = time.time()
    alert_display_timer = 0
    show_alert = False
    alert_text = ""
    
    while monitoring_active:
        try:
            # Read frame from camera
            success, frame = camera.read_frame()
            if not success:
                continue
            
            # Add frame to evidence buffer
            evidence_manager.add_frame_to_buffer(frame)
            
            # Detect objects
            results, annotated_frame = detector.detect_objects(frame)
            detections = detector.extract_detections(results)
            
            # Analyze for dumping
            analysis = dumping_detector.analyze_frame(detections, frame)
            
            # Calculate cleanliness
            score, rating, garbage_count, color = cleanliness_monitor.calculate_cleanliness_score(
                detections, frame.shape
            )
            
            # Count persons
            persons_count = len([d for d in detections if d['object'] == 'person'])
            
            # Update statistics
            current_stats['cleanliness_score'] = round(score, 1)
            current_stats['rating'] = rating
            current_stats['garbage_count'] = garbage_count
            current_stats['persons_count'] = persons_count
            current_stats['monitoring_time'] = int(time.time() - start_time)
            current_stats['is_recording'] = evidence_manager.is_recording
            
            # If dumping detected
            if analysis['dumping_detected']:
                # Save evidence
                evidence_data = evidence_manager.save_evidence(
                    analysis['dumping_info'],
                    location_name="Web Monitoring - Main Campus"
                )
                
                # Generate alert
                alert_data = alert_system.create_alert(
                    analysis['dumping_info'],
                    location_name="Web Monitoring - Main Campus",
                    evidence_path=evidence_data['image_path'] if evidence_data else None
                )
                
                # Update stats
                current_stats['total_incidents'] += 1
                current_stats['total_alerts'] += 1
                
                # Show alert
                show_alert = True
                alert_display_timer = 150
                alert_text = f"{alert_data['object']} detected - {alert_data['alert_id']}"
                
                # Emit alert to web clients
                socketio.emit('new_alert', {
                    'object': alert_data['object'],
                    'timestamp': alert_data['timestamp'],
                    'alert_id': alert_data['alert_id'],
                    'confidence': analysis['dumping_info']['confidence']
                })
            
            # If recording video, add frames
            if evidence_manager.is_recording:
                evidence_manager.add_frame_to_video(annotated_frame)
            
            # Update cleanliness monitoring
            cleanliness_monitor.update_session(
                detections,
                frame.shape,
                dumping_detected=analysis['dumping_detected']
            )
            
            # Draw visualizations
            final_frame = dumping_detector.draw_analysis(annotated_frame, detections, analysis)
            final_frame = cleanliness_monitor.draw_cleanliness_info(final_frame, detections)
            
            # Add recording indicator
            if evidence_manager.is_recording:
                cv2.circle(final_frame, (final_frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
                cv2.putText(final_frame, "REC", 
                           (final_frame.shape[1] - 70, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Countdown alert timer
            if alert_display_timer > 0:
                alert_display_timer -= 1
                if alert_display_timer == 0:
                    show_alert = False
            
            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', final_frame)
            frame_bytes = buffer.tobytes()
            
            # Encode to base64 for web transmission
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
            
            # Emit frame to web clients
            socketio.emit('video_frame', {'frame': frame_base64})
            
            # Emit stats update
            socketio.emit('stats_update', current_stats)
            
            # Small delay to control frame rate
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            continue

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    """Start the monitoring system"""
    global monitoring_active, monitoring_thread, current_stats
    
    with thread_lock:
        if monitoring_active:
            return jsonify({'status': 'error', 'message': 'Already monitoring'})
        
        # Reset stats
        current_stats = {
            'cleanliness_score': 100,
            'rating': 'Excellent',
            'garbage_count': 0,
            'persons_count': 0,
            'total_incidents': 0,
            'total_alerts': 0,
            'monitoring_time': 0,
            'is_recording': False
        }
        
        # Initialize system
        if not initialize_system():
            return jsonify({'status': 'error', 'message': 'Failed to initialize system'})
        
        # Start monitoring thread
        monitoring_active = True
        monitoring_thread = Thread(target=monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        return jsonify({'status': 'success', 'message': 'Monitoring started'})

@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring system and generate report"""
    global monitoring_active, camera
    
    with thread_lock:
        if not monitoring_active:
            return jsonify({'status': 'error', 'message': 'Not monitoring'})
        
        monitoring_active = False
        
        # Give monitoring loop time to finish
        time.sleep(0.5)
        
        # Stop video recording if active
        if evidence_manager and evidence_manager.is_recording:
            evidence_manager.stop_video_recording()
        
        # Finalize cleanliness session
        if cleanliness_monitor:
            print("📊 Finalizing cleanliness session...")
            cleanliness_monitor.finalize_session(location_name="Web Monitoring - Main Campus")
        
        # Generate comprehensive report
        if cleanliness_monitor and evidence_manager and alert_system:
            try:
                print("📄 Generating comprehensive report...")
                report_gen = ReportGenerator(reports_folder='reports')
                
                cleanliness_data = {
                    'current_session': cleanliness_monitor.current_session,
                    'history': cleanliness_monitor.history
                }
                evidence_data = evidence_manager.get_evidence_summary()
                alert_data = alert_system.get_session_summary()
                
                report_path = report_gen.generate_report(
                    cleanliness_data,
                    evidence_data,
                    alert_data,
                    location_name="Web Monitoring - Main Campus"
                )
                
                if report_path:
                    print(f"✅ Report generated: {report_path}")
                else:
                    print("⚠️ Report generation returned None")
                    
            except Exception as e:
                print(f"❌ Error generating report: {e}")
        
        # Release camera
        if camera:
            camera.release()
        
        return jsonify({'status': 'success', 'message': 'Monitoring stopped and report generated'})

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    return jsonify(current_stats)

@app.route('/api/evidence')
def get_evidence():
    """Get list of evidence files"""
    evidence_files = []
    
    if os.path.exists('evidence'):
        for filename in os.listdir('evidence'):
            if filename.endswith(('.jpg', '.png', '.avi', '.mp4')):
                filepath = os.path.join('evidence', filename)
                file_stats = os.stat(filepath)
                
                evidence_files.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'timestamp': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'video' if filename.endswith(('.avi', '.mp4')) else 'image'
                })
    
    # Sort by timestamp (newest first)
    evidence_files.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(evidence_files)

@app.route('/api/alerts')
def get_alerts():
    """Get list of recent alerts"""
    alerts = []
    
    if alert_system and hasattr(alert_system, 'session_alerts'):
        for alert in alert_system.session_alerts:
            alerts.append({
                'alert_id': alert['alert_id'],
                'timestamp': alert['timestamp'],
                'object': alert['object'],
                'confidence': alert['confidence'],
                'location': alert['location']
            })
    
    return jsonify(alerts)

@app.route('/api/reports')
def get_reports():
    """Get list of generated reports"""
    reports = []
    
    if os.path.exists('reports'):
        for filename in os.listdir('reports'):
            if filename.startswith('Cleanliness_Report_') and filename.endswith('.txt'):
                filepath = os.path.join('reports', filename)
                file_stats = os.stat(filepath)
                
                reports.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'timestamp': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(reports)

@app.route('/api/report/<filename>')
def get_report_content(filename):
    """Get content of a specific report with encoding error handling"""
    try:
        filepath = os.path.join('reports', filename)
        if os.path.exists(filepath):
            # Try multiple encodings to handle different file formats
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    break  # Success, exit loop
                except (UnicodeDecodeError, LookupError):
                    continue  # Try next encoding
            
            if content is None:
                # If all encodings failed, read as binary and decode with replacement
                with open(filepath, 'rb') as f:
                    content = f.read().decode('utf-8', errors='replace')
            
            return jsonify({'content': content, 'filename': filename})
        else:
            return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        print(f"Error reading report: {e}")
        return jsonify({'error': f'Error reading report: {str(e)}'}), 500

@app.route('/api/alert/<filename>')
def get_alert_content(filename):
    """Get content of a specific alert file with encoding error handling"""
    try:
        filepath = os.path.join('reports', filename)
        if os.path.exists(filepath):
            # Try multiple encodings to handle different file formats
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    break  # Success, exit loop
                except (UnicodeDecodeError, LookupError):
                    continue  # Try next encoding
            
            if content is None:
                # If all encodings failed, read as binary and decode with replacement
                with open(filepath, 'rb') as f:
                    content = f.read().decode('utf-8', errors='replace')
            
            return jsonify({'content': content, 'filename': filename})
        else:
            return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        print(f"Error reading alert: {e}")
        return jsonify({'error': f'Error reading alert: {str(e)}'}), 500

@app.route('/api/dumping_log')
def get_dumping_log():
    """Get dumping log content with encoding error handling"""
    try:
        log_path = 'evidence/dumping_log.txt'
        if os.path.exists(log_path):
            # Try multiple encodings to handle different file formats
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(log_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    break  # Success, exit loop
                except (UnicodeDecodeError, LookupError):
                    continue  # Try next encoding
            
            if content is None:
                # If all encodings failed, read as binary and decode with replacement
                with open(log_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='replace')
            
            return jsonify({'content': content})
        else:
            return jsonify({'content': 'No log file found.'})
    except Exception as e:
        print(f"Error reading log: {e}")
        return jsonify({'error': f'Error reading log: {str(e)}'}), 500

@app.route('/api/cleanliness_history')
def get_cleanliness_history():
    """Get cleanliness history data"""
    try:
        history_path = 'data/cleanliness_history.json'
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return jsonify(history)
        else:
            return jsonify({'sessions': []})
    except Exception as e:
        print(f"Error reading history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert_files')
def get_alert_files():
    """Get list of all alert files"""
    alerts = []
    
    if os.path.exists('reports'):
        for filename in os.listdir('reports'):
            if filename.startswith('ALERT-') and filename.endswith('.txt'):
                filepath = os.path.join('reports', filename)
                file_stats = os.stat(filepath)
                
                alerts.append({
                    'filename': filename,
                    'alert_id': filename.replace('.txt', ''),
                    'size': file_stats.st_size,
                    'timestamp': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(alerts)

@app.route('/api/settings/email', methods=['GET'])
def get_email_settings():
    """Get current recipient email"""
    try:
        if alert_system and hasattr(alert_system, 'email_config'):
            return jsonify({
                'status': 'success', 
                'recipient': alert_system.email_config.get('recipient', '')
            })
        else:
            return jsonify({'status': 'error', 'message': 'Alert system not initialized'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/email', methods=['POST'])
def save_email_settings():
    """Save recipient email configuration"""
    try:
        if not alert_system:
            return jsonify({'status': 'error', 'message': 'Alert system not initialized'}), 400
        
        data = request.get_json()
        
        # Validate recipient field
        if 'recipient' not in data:
            return jsonify({'status': 'error', 'message': 'Missing recipient email'}), 400
        
        recipient = data['recipient'].strip()
        
        # Basic email validation
        if not recipient or '@' not in recipient:
            return jsonify({'status': 'error', 'message': 'Invalid email address'}), 400
        
        # Save recipient email
        if alert_system.save_config(recipient):
            return jsonify({'status': 'success', 'message': 'Recipient email saved successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to save recipient email'}), 500
            
    except Exception as e:
        print(f"Error saving recipient email: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/evidence/<path:filename>')

def serve_evidence(filename):
    """Serve evidence files"""
    return send_from_directory('../evidence', filename)

@app.route('/reports/<path:filename>')
def serve_report(filename):
    """Serve report files"""
    return send_from_directory('../reports', filename)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SMART CAMPUS MONITORING SYSTEM - WEB APPLICATION")
    print("="*80)
    print("\n🌐 Starting web server...")
    print("📍 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

app.py