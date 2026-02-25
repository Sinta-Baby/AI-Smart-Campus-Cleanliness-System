#  AI-Based Smart Campus Cleanliness & Illegal Dumping Monitoring System

An intelligent real-time surveillance system that detects illegal waste dumping on campus using Computer Vision and YOLOv8.

---

##  Project Overview

The AI Smart Campus Cleanliness System is designed to monitor campus areas using camera feeds and automatically detect illegal dumping activities.

When dumping is detected, the system:

• Triggers 3 alert beeps  
• Plays a voice warning ("Violation detected")  
• Displays a visual alert banner  
• Saves evidence (image + report file)  
• Sends email notification  
• Logs the incident  

This system helps improve campus cleanliness and accountability using AI.

---

##  Technologies Used

- Python
- OpenCV
- YOLOv8 (Ultralytics)
- SMTP (Email Alerts)
- Threading
- Windows PowerShell (Voice Alert)
- HTML (Web Interface)

---

##  Features

✅ Real-time object detection  
✅ Illegal dumping detection logic  
✅ 3-Beep alert system  
✅ Voice alert system  
✅ Email notification system  
✅ Evidence capture and storage  
✅ Alert log generation  
✅ Session summary report  

---

##  Project Structure

SmartCampusCleanliness/
│
├── src/ # Core detection and alert modules
├── webapp/ # Web interface components
├── data/ # Configuration or dataset files
├── requirements.txt # Project dependencies
├── .gitignore
└── README.md



---

## Environment Configuration

Create a `.env` file in the project root directory with the following variables:
EMAIL_SENDER=your_email@gmail.com

EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient_email@gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587



Note: The `.env` file is excluded from version control for security purposes.

---

## Installation and Setup

1. Clone the repository:git clone https://github.com/Sinta-Baby/AI-Smart-Campus-Cleanliness-System.git
2. Navigate to the project directory:cd AI-Smart-Campus-Cleanliness-System
3. Install the required dependencies:pip install -r requirements.txt
4. Run the application:python main.py


---

## Future Improvements

- Multi-category waste detection  
- Cloud storage integration  
- Administrative dashboard  
- SMS and mobile push notifications  
- Model performance optimization  

---

## Author

Developed by **CeeQ — Where Code Meets Cognition**(group project )

---

## License

This project is intended for academic and research purposes.


