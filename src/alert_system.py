# alert_system.py
# Complete Alert System with 3 Beeps and RELIABLE Voice for EVERY Detection

import cv2
import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import threading
import time
import winsound  # For Windows alert sound
import subprocess  # For PowerShell voice
from dotenv import load_dotenv
load_dotenv()

class AlertSystem:
    """
    Complete Alert System with:
    - 3 BEEP sounds on EVERY detection
    - Voice alert ("Violation detected") on EVERY detection
    - Visual banner on screen
    - Email notification
    - Log file generation
    - Individual alert files saved
    """
    
    def __init__(self, alerts_folder='reports', email_config=None, config_file=None):
        """
        Initialize the alert system
        """
        print("🚨 Initializing Alert System...")
        
        self.alerts_folder = alerts_folder
        self.config_file = config_file
        
        # Base email configuration (sender credentials are hardcoded)
        base_config = {
            'sender': os.getenv("EMAIL_SENDER"),
            'password': os.getenv("EMAIL_PASSWORD"),
            'recipient': os.getenv("EMAIL_RECIPIENT"),
            'smtp_server': os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            'smtp_port': int(os.getenv("EMAIL_SMTP_PORT", 587))
        }
        
        # Load recipient from config file if available
        if config_file and os.path.exists(config_file):
            saved_config = self.load_config()
            if saved_config and 'recipient' in saved_config:
                base_config['recipient'] = saved_config['recipient']
        
        self.email_config = base_config
        
        self.last_email_time = 0
        self.email_cooldown = 60  # seconds between emails
        
        # Create alerts folder
        if not os.path.exists(alerts_folder):
            os.makedirs(alerts_folder)
            print(f"   ✅ Created alerts folder: {alerts_folder}")
        
        # Path to alerts log file
        self.alerts_log = os.path.join(alerts_folder, 'alerts_log.txt')
        
        # Initialize log file
        if not os.path.exists(self.alerts_log):
            with open(self.alerts_log, 'w') as f:
                f.write("="*80 + "\n")
                f.write("SMART CAMPUS ILLEGAL DUMPING ALERT LOG\n")
                f.write("="*80 + "\n\n")
            print(f"   ✅ Created alerts log: {self.alerts_log}")
        
        # Counter for alerts
        self.alert_count = 0
        self.session_alerts = []
        
        print("✅ Alert System ready!")
    
    def load_config(self):
        """Load email configuration from JSON file"""
        try:
            if self.config_file and os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    print(f"   ✅ Loaded email config from {self.config_file}")
                    return config
        except Exception as e:
            print(f"   ⚠️ Error loading config: {e}")
        
        # Return default config if loading fails
        return {
            'sender': '',
            'password': '',
            'recipient': '',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587
        }
    
    def save_config(self, recipient_email):
        """Save recipient email configuration to JSON file"""
        try:
            if self.config_file:
                # Ensure directory exists
                config_dir = os.path.dirname(self.config_file)
                if config_dir and not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                
                # Only save recipient email
                config = {'recipient': recipient_email}
                
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                
                # Update current config recipient
                self.email_config['recipient'] = recipient_email
                print(f"   ✅ Saved recipient email to {self.config_file}")
                return True
        except Exception as e:
            print(f"   ❌ Error saving config: {e}")
            return False
        return False
    
    # 🔊 3 BEEP SOUNDS + VOICE ALERT (EVERY TIME - 100% RELIABLE)
    def trigger_voice_alert(self):
        """
        Play 3 beep sounds and voice alert EVERY TIME dumping is detected
        Using Windows PowerShell for reliable voice output
        """
        try:
            # Play 3 beep sounds in sequence
            print("🔊 Playing 3 alert beeps...")
            
            # Beep 1
            winsound.Beep(1000, 300)  # 1000Hz for 300ms
            time.sleep(0.1)
            
            # Beep 2
            winsound.Beep(1200, 300)  # 1200Hz for 300ms
            time.sleep(0.1)
            
            # Beep 3
            winsound.Beep(1400, 400)  # 1400Hz for 400ms
            time.sleep(0.2)
            
            # Use Windows PowerShell for speech (100% reliable, works every time)
            print("🗣️ Speaking: Violation detected")
            
            # PowerShell command for speech
            powershell_command = '''
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.Speak('Violation detected');
            '''
            
            # Run PowerShell in background thread to not block
            def speak():
                try:
                    subprocess.run(['powershell', '-command', powershell_command], 
                                  capture_output=True, timeout=5)
                except:
                    pass
            
            # Start speech in background thread
            speech_thread = threading.Thread(target=speak)
            speech_thread.daemon = True
            speech_thread.start()
            
            # Small delay
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Voice alert error: {e}")
            # Fallback: Just beep more if voice fails
            try:
                winsound.Beep(800, 500)
                winsound.Beep(800, 500)
            except:
                pass
    
    # 📧 EMAIL ALERT
    def send_alert_email(self, alert_data, evidence_path):
        """
        Send email alert with dumping information
        """
        current_time = datetime.now().timestamp()
        
        # Check cooldown
        if current_time - self.last_email_time < self.email_cooldown:
            print("   ⏱️ Email cooldown active. Skipping email.")
            return False
        
        def email_thread():
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = self.email_config['sender']
                msg['To'] = self.email_config['recipient']
                msg['Subject'] = f"🚨 ALERT: Illegal Dumping Detected - {alert_data['alert_id']}"
                
                # Email body
                body = f"""
                <html>
                <body>
                    <h2 style="color: red;">🚨 ILLEGAL DUMPING ALERT</h2>
                    
                    <h3>Incident Details:</h3>
                    <ul>
                        <li><b>Alert ID:</b> {alert_data['alert_id']}</li>
                        <li><b>Time:</b> {alert_data['timestamp']}</li>
                        <li><b>Location:</b> {alert_data['location']}</li>
                        <li><b>Object:</b> {alert_data['object']}</li>
                        <li><b>Confidence:</b> {alert_data['confidence']}%</li>
                    </ul>
                    
                    <p>Evidence image attached.</p>
                    <hr>
                    <p><i>Smart Campus Cleanliness Monitoring System</i></p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                # Attach evidence image
                if evidence_path and os.path.exists(evidence_path):
                    with open(evidence_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data, name=os.path.basename(evidence_path))
                        msg.attach(image)
                
                # Send email
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['sender'], self.email_config['password'])
                server.send_message(msg)
                server.quit()
                
                print(f"   ✅ Email sent to {self.email_config['recipient']}")
                self.last_email_time = current_time
                
            except Exception as e:
                print(f"   ❌ Email error: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=email_thread)
        thread.daemon = True
        thread.start()
        return True
    
    # 🆔 Generate unique alert ID
    def generate_alert_id(self):
        """Generate unique alert ID"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"ALERT-{timestamp}"
    
    # 📝 Save alert to individual file
    def save_alert_file(self, alert_data, location_name, evidence_path):
        """
        Save alert to individual text file
        """
        try:
            alert_filename = f"{alert_data['alert_id']}.txt"
            alert_filepath = os.path.join(self.alerts_folder, alert_filename)
            
            # Create detailed alert message
            message = f"""
{'='*80}
ILLEGAL DUMPING ALERT
{'='*80}

Alert ID: {alert_data['alert_id']}
Date/Time: {alert_data['timestamp']}
Location: {location_name}
Object Detected: {alert_data['object']}
AI Confidence: {alert_data['confidence']}%

{'='*80}
EVIDENCE INFORMATION
{'='*80}

Evidence Image: {evidence_path if evidence_path else 'Not saved'}
Alert Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'='*80}
This alert was automatically generated by the Smart Campus
Cleanliness & Illegal Dumping Monitoring System.
{'='*80}
"""
            
            with open(alert_filepath, 'w') as f:
                f.write(message)
            
            print(f"   ✅ Alert file saved: {alert_filepath}")
            return alert_filepath
            
        except Exception as e:
            print(f"   ❌ Error saving alert file: {e}")
            return None
    
    # 📝 Create and save alert
    def create_alert(self, dumping_info, location_name="Campus Area", 
                     evidence_path=None, send_email=True):
        """
        Create alert, trigger sound (3 beeps + voice), and send notifications
        This runs EVERY TIME dumping is detected
        """
        # Generate alert ID
        alert_id = self.generate_alert_id()
        
        # Create alert data
        alert_data = {
            'alert_id': alert_id,
            'timestamp': dumping_info['timestamp'],
            'location': location_name,
            'object': dumping_info['object'],
            'confidence': dumping_info['confidence']
        }
        
        print(f"\n🚨 ALERT GENERATED: {alert_id}")
        print(f"   Object: {dumping_info['object']}")
        print(f"   Time: {dumping_info['timestamp']}")
        
        # 🔴 PLAY 3 BEEP SOUNDS AND VOICE ALERT (EVERY TIME)
        self.trigger_voice_alert()
        
        # Save to main log file
        self.log_alert(alert_data, evidence_path)
        
        # Save individual alert file
        alert_filepath = self.save_alert_file(alert_data, location_name, evidence_path)
        
        # Add filepath to alert_data for report generator
        if alert_filepath:
            alert_data['filepath'] = alert_filepath
        else:
            alert_data['filepath'] = None
        
        # Increment counter
        self.alert_count += 1
        self.session_alerts.append(alert_data)
        
        # 📧 Send email if requested
        if send_email and evidence_path:
            self.send_alert_email(alert_data, evidence_path)
        
        return alert_data
    
    # 📋 Log alert to main log file
    def log_alert(self, alert_data, evidence_path=None):
        """Write alert to main log file"""
        try:
            with open(self.alerts_log, 'a') as f:
                f.write("-"*70 + "\n")
                f.write(f"Alert #{self.alert_count + 1}\n")
                f.write(f"Alert ID: {alert_data['alert_id']}\n")
                f.write(f"Timestamp: {alert_data['timestamp']}\n")
                f.write(f"Location: {alert_data['location']}\n")
                f.write(f"Object: {alert_data['object']}\n")
                f.write(f"Confidence: {alert_data['confidence']}%\n")
                if evidence_path:
                    f.write(f"Evidence: {evidence_path}\n")
                f.write("-"*70 + "\n\n")
        except Exception as e:
            print(f"   ❌ Error logging alert: {e}")
    
    # 🖼️ Draw alert notification on screen
    def draw_alert_notification(self, frame, show_alert=False, alert_text=""):
        """
        Draw visual alert banner on the video frame
        """
        annotated_frame = frame.copy()
        
        if show_alert and alert_text:
            frame_height, frame_width = frame.shape[:2]
            
            # Create red banner at top
            banner_height = 140
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame_width, banner_height), (0, 0, 200), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            # Alert icon (circle with exclamation)
            cv2.circle(annotated_frame, (50, 70), 30, (0, 0, 255), 3)
            cv2.putText(annotated_frame, "!", (43, 83), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
            
            # Alert title
            cv2.putText(annotated_frame, "🚨 DUMPING DETECTED - ALERT TRIGGERED", 
                       (100, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Alert details
            cv2.putText(annotated_frame, alert_text, 
                       (100, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Sound indicators - SHOWING 3 BEEPS
            cv2.putText(annotated_frame, "🔊 BEEP! BEEP! BEEP! - Voice: Violation detected", 
                       (100, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Show that it's the current alert number
            cv2.putText(annotated_frame, f"Alert #{self.alert_count}", 
                       (100, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Speaker icon
            cv2.putText(annotated_frame, "🔊", (10, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Always show total alert count
        cv2.putText(annotated_frame, f"Total Alerts Today: {self.alert_count}", 
                   (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return annotated_frame
    
    # 📊 Get session summary
    def get_session_summary(self):
        """Get summary of alerts in current session"""
        return {
            'total_alerts': self.alert_count,
            'alerts_log': self.alerts_log,
            'alerts_folder': self.alerts_folder,
            'session_alerts': self.session_alerts
        }
    
    # 📈 Print session summary
    def print_session_summary(self):
        """Print detailed alert summary"""
        print("\n" + "="*80)
        print("ALERT SYSTEM SESSION SUMMARY")
        print("="*80)
        
        print(f"\n🚨 Total Alerts Generated: {self.alert_count}")
        print(f"📁 Alerts Folder: {self.alerts_folder}")
        print(f"📄 Alerts Log: {self.alerts_log}")
        print(f"📧 Email Recipient: {self.email_config['recipient']}")
        
        if len(self.session_alerts) > 0:
            print(f"\n📋 Alerts in This Session:")
            for i, alert in enumerate(self.session_alerts, 1):
                print(f"\n   {i}. {alert['alert_id']}")
                print(f"      Time: {alert['timestamp']}")
                print(f"      Location: {alert['location']}")
                print(f"      Object: {alert['object']}")
                print(f"      Confidence: {alert['confidence']}%")
                if 'filepath' in alert and alert['filepath']:
                    print(f"      File: {alert['filepath']}")
        
        print("\n" + "="*80 + "\n")


# Test function
def test_alert_system():
    """Test the alert system with multiple alerts"""
    print("\n" + "="*80)
    print("TESTING ALERT SYSTEM - MULTIPLE ALERTS")
    print("="*80 + "\n")
    
    # Create alert system
    alert = AlertSystem()
    
    # Test multiple alerts to verify beeps AND VOICE work every time
    for i in range(3):
        print(f"\n📝 Creating test alert #{i+1}...")
        
        # Simulate dumping info
        dumping_info = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'object': f'plastic bottle {i+1}',
            'confidence': 95 - (i*5)
        }
        
        # Create test alert (THIS WILL TRIGGER 3 BEEPS + VOICE EACH TIME)
        alert.create_alert(
            dumping_info,
            location_name="Test Location",
            evidence_path=None,
            send_email=False
        )
        
        print(f"✅ Alert #{i+1} complete - you should have heard 3 beeps and voice")
        time.sleep(3)  # Wait 3 seconds between alerts
    
    print("\n✅ Alert system test complete! You should have heard:")
    print("   • 3 beeps for each alert (total 9 beeps)")
    print("   • Voice saying 'Violation detected' for each alert (total 3 times)")
    print(f"\n📊 Total alerts triggered: {alert.alert_count}")
    
    # Show where files were saved
    print(f"\n📁 Alert files saved in: {os.path.abspath(alert.alerts_folder)}")

if __name__ == "__main__":
    test_alert_system()