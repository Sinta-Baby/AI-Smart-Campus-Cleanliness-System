# report_generator.py
# This module generates professional cleanliness reports

import os
import json
from datetime import datetime
from collections import Counter

class ReportGenerator:
    """
    A class to generate cleanliness and incident reports
    """
    
    def __init__(self, reports_folder='reports'):
        """
        Initialize the report generator
        
        Args:
            reports_folder: Folder to store generated reports
        """
        print("📊 Initializing Report Generator...")
        
        self.reports_folder = reports_folder
        
        # Create reports folder if it doesn't exist
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)
            print(f"   ✅ Created reports folder: {reports_folder}")
        
        print("✅ Report Generator ready!")
    
    def generate_report(self, cleanliness_data, evidence_data, alert_data, 
                       location_name="Campus Area"):
        """
        Generate a comprehensive cleanliness report
        
        Args:
            cleanliness_data: Data from CleanlinessMonitor
            evidence_data: Data from EvidenceManager
            alert_data: Data from AlertSystem
            location_name: Name of monitored location
            
        Returns:
            report_path: Path to generated report file
        """
        print("\n📝 Generating comprehensive report...")
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"Cleanliness_Report_{timestamp}.txt"
        report_path = os.path.join(self.reports_folder, report_filename)
        
        # Build report content
        report = self._build_report_content(
            cleanliness_data, evidence_data, alert_data, location_name
        )
        
        # Save report
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"   ✅ Report saved: {report_path}")
            return report_path
        except Exception as e:
            print(f"   ❌ Error saving report: {e}")
            return None
    
    def _build_report_content(self, cleanliness_data, evidence_data, 
                             alert_data, location_name):
        """
        Build the complete report content
        
        Args:
            cleanliness_data: Cleanliness monitoring data
            evidence_data: Evidence summary data
            alert_data: Alert system data
            location_name: Location name
            
        Returns:
            report: Complete report as string
        """
        # Get current session data
        session = cleanliness_data['current_session']
        samples = session['cleanliness_samples']
        
        # Calculate metrics
        if len(samples) > 0:
            scores = [s['score'] for s in samples]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            # Calculate rating distribution
            excellent = sum(1 for s in scores if s >= 90)
            good = sum(1 for s in scores if 70 <= s < 90)
            fair = sum(1 for s in scores if 50 <= s < 70)
            poor = sum(1 for s in scores if s < 50)
            total_samples = len(scores)
            
            # Determine overall rating
            if avg_score >= 90:
                overall_rating = "Excellent"
            elif avg_score >= 70:
                overall_rating = "Good"
            elif avg_score >= 50:
                overall_rating = "Fair"
            else:
                overall_rating = "Poor"
        else:
            avg_score = 100
            max_score = 100
            min_score = 100
            overall_rating = "Excellent"
            excellent = 1
            good = fair = poor = 0
            total_samples = 1
        
        # Build report
        report = f"""
{'='*80}
                    CAMPUS CLEANLINESS REPORT
{'='*80}
Report Period: {session['start_time']} to {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Location: {location_name}

{'='*80}
EXECUTIVE SUMMARY
{'='*80}
Overall Cleanliness Rating: {overall_rating} ({avg_score:.1f}%)
Total Frames Analyzed: {session['frames_analyzed']:,}
Total Garbage Detections: {session['garbage_detections']}
Dumping Incidents Detected: {session['dumping_events']}
Alerts Generated: {alert_data['total_alerts']}

{'='*80}
CLEANLINESS METRICS
{'='*80}
Average Cleanliness Score: {avg_score:.1f}%
Highest Score: {max_score:.1f}% ({self._get_rating_text(max_score)})
Lowest Score: {min_score:.1f}% ({self._get_rating_text(min_score)})

Rating Distribution:
  • Excellent (90-100%): {(excellent/total_samples*100):.1f}% of samples ({excellent} samples)
  • Good (70-89%):       {(good/total_samples*100):.1f}% of samples ({good} samples)
  • Fair (50-69%):       {(fair/total_samples*100):.1f}% of samples ({fair} samples)
  • Poor (0-49%):        {(poor/total_samples*100):.1f}% of samples ({poor} samples)

{'='*80}
INCIDENT REPORT
{'='*80}
Total Incidents: {session['dumping_events']}
Total Evidence Files: {evidence_data['total_incidents']}

"""
        # Add individual incidents (FIXED VERSION - handles missing filepath)
        if len(alert_data['session_alerts']) > 0:
            for i, alert in enumerate(alert_data['session_alerts'], 1):
                # Safely get evidence filename
                evidence_display = "Not available"
                alert_file_display = "Not available"
                
                # Check if evidence_path exists in alert_data
                if 'evidence_path' in alert and alert['evidence_path']:
                    evidence_display = os.path.basename(alert['evidence_path'])
                elif 'filepath' in alert and alert['filepath']:
                    # Try to derive evidence from alert file
                    evidence_display = os.path.basename(alert['filepath']).replace('.txt', '.jpg')
                    alert_file_display = alert['filepath']
                else:
                    # Look for evidence in evidence folder with similar timestamp
                    evidence_display = f"evidence_{alert['alert_id']}.jpg"
                    alert_file_display = f"reports/{alert['alert_id']}.txt"
                
                report += f"""
Incident #{i}:
  Time: {alert['timestamp']}
  Object: {alert['object']}
  Confidence: {alert['confidence']}%
  Evidence File: {evidence_display}
  Alert ID: {alert['alert_id']}
  Alert File: {alert_file_display}
"""
        else:
            report += "\nNo incidents detected during this monitoring period.\n"
        
        # Add recommendations
        report += f"""
{'='*80}
RECOMMENDATIONS
{'='*80}
Based on the analysis:

"""
        
        # Generate recommendations based on data
        recommendations = self._generate_recommendations(
            avg_score, session['dumping_events'], overall_rating
        )
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
{'='*80}
DETAILED CLEANLINESS SAMPLES
{'='*80}
"""
        
        # Add sample history (show last 10 samples)
        if len(samples) > 0:
            recent_samples = samples[-10:]  # Last 10 samples
            report += "\nRecent Cleanliness Measurements:\n\n"
            
            for sample in recent_samples:
                report += f"  {sample['timestamp']} - Score: {sample['score']:.1f}% "
                report += f"({sample['rating']}) - Garbage: {sample['garbage_count']}\n"
        else:
            report += "\nNo samples recorded during this period.\n"
        
        report += f"""
{'='*80}
SYSTEM INFORMATION
{'='*80}
Evidence Storage: {evidence_data['evidence_folder']}
Evidence Log: {evidence_data.get('log_file', 'Not available')}
Alerts Storage: {alert_data['alerts_folder']}
Alerts Log: {alert_data['alerts_log']}

{'='*80}
ALERT SYSTEM SUMMARY
{'='*80}
Total Alerts Triggered: {alert_data['total_alerts']}
Alerts Folder: {alert_data['alerts_folder']}
Last Alert: {alert_data['session_alerts'][-1]['timestamp'] if alert_data['session_alerts'] else 'None'}

{'='*80}
End of Report
{'='*80}

This report was automatically generated by the Smart Campus Cleanliness
& Illegal Dumping Monitoring System.

For questions or concerns, please contact Campus Management.
"""
        
        return report
    
    def _get_rating_text(self, score):
        """
        Get rating text for a score
        
        Args:
            score: Cleanliness score
            
        Returns:
            rating: Rating text
        """
        if score >= 90:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_recommendations(self, avg_score, incidents, rating):
        """
        Generate recommendations based on data
        
        Args:
            avg_score: Average cleanliness score
            incidents: Number of incidents
            rating: Overall rating
            
        Returns:
            recommendations: List of recommendation strings
        """
        recommendations = []
        
        # Score-based recommendations
        if avg_score >= 90:
            recommendations.append(
                f"Overall cleanliness is {rating} - maintain current practices"
            )
        elif avg_score >= 70:
            recommendations.append(
                f"Overall cleanliness is {rating} - minor improvements recommended"
            )
        elif avg_score >= 50:
            recommendations.append(
                f"Overall cleanliness is {rating} - improvements needed"
            )
        else:
            recommendations.append(
                f"Overall cleanliness is {rating} - immediate action required"
            )
        
        # Incident-based recommendations
        if incidents == 0:
            recommendations.append(
                "No dumping incidents detected - excellent compliance"
            )
        elif incidents <= 2:
            recommendations.append(
                f"{incidents} dumping incident(s) detected - consider additional signage"
            )
        elif incidents <= 5:
            recommendations.append(
                f"{incidents} dumping incidents detected - increase monitoring frequency"
            )
        else:
            recommendations.append(
                f"{incidents} dumping incidents detected - urgent intervention needed"
            )
        
        # General recommendations
        if incidents > 0:
            recommendations.append(
                "Review evidence files to identify repeat offenders"
            )
            recommendations.append(
                "Consider installing additional surveillance cameras in problem areas"
            )
        
        recommendations.append(
            "Continue regular monitoring to maintain campus cleanliness standards"
        )
        
        return recommendations
    
    def print_report_summary(self, report_path):
        """
        Print summary after report generation
        
        Args:
            report_path: Path to generated report
        """
        print("\n" + "="*80)
        print("REPORT GENERATION COMPLETE")
        print("="*80)
        print(f"\n📄 Report saved to: {report_path}")
        print(f"📁 Reports folder: {self.reports_folder}")
        print("\nYou can:")
        print("  • Open the report file to view full details")
        print("  • Print the report for physical records")
        print("  • Email the report to campus management")
        print("  • Archive the report for future reference")
        print("\n" + "="*80 + "\n")


def test_report_generator():
    """
    Test complete system with report generation
    """
    print("\n" + "="*80)
    print("TESTING COMPLETE SYSTEM WITH REPORT GENERATION")
    print("="*80 + "\n")
    
    # Create mock data for testing
    from datetime import datetime, timedelta
    
    # Mock cleanliness data
    cleanliness_data = {
        'current_session': {
            'start_time': (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            'frames_analyzed': 3600,
            'garbage_detections': 45,
            'dumping_events': 3,
            'cleanliness_samples': [
                {'timestamp': (datetime.now() - timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 85.5, 'rating': 'Good', 'garbage_count': 2},
                {'timestamp': (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 72.3, 'rating': 'Good', 'garbage_count': 3},
                {'timestamp': (datetime.now() - timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 68.7, 'rating': 'Fair', 'garbage_count': 4},
                {'timestamp': (datetime.now() - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 91.2, 'rating': 'Excellent', 'garbage_count': 1},
                {'timestamp': (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 78.9, 'rating': 'Good', 'garbage_count': 2},
                {'timestamp': (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), 
                 'score': 82.4, 'rating': 'Good', 'garbage_count': 2},
            ]
        },
        'history': []
    }
    
    # Mock evidence data
    evidence_data = {
        'total_incidents': 3,
        'total_videos': 2,
        'evidence_folder': 'evidence',
        'log_file': 'evidence/dumping_log.txt',
        'session_saves': 3,
        'video_enabled': True
    }
    
    # Mock alert data with filepaths
    alert_data = {
        'total_alerts': 3,
        'alerts_log': 'reports/alerts_log.txt',
        'alerts_folder': 'reports',
        'session_alerts': [
            {
                'alert_id': 'ALERT-20250216-103245',
                'timestamp': (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
                'location': 'Main Campus - Test Area',
                'object': 'plastic bottle',
                'confidence': 95,
                'filepath': 'reports/ALERT-20250216-103245.txt',
                'evidence_path': 'evidence/2025-02-16_10-32-45_plastic_bottle.jpg'
            },
            {
                'alert_id': 'ALERT-20250216-104512',
                'timestamp': (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                'location': 'Main Campus - Test Area',
                'object': 'food wrapper',
                'confidence': 87,
                'filepath': 'reports/ALERT-20250216-104512.txt',
                'evidence_path': 'evidence/2025-02-16_10-45-12_food_wrapper.jpg'
            },
            {
                'alert_id': 'ALERT-20250216-105823',
                'timestamp': (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                'location': 'Main Campus - Test Area',
                'object': 'plastic cup',
                'confidence': 92,
                'filepath': 'reports/ALERT-20250216-105823.txt',
                'evidence_path': 'evidence/2025-02-16_10-58-23_plastic_cup.jpg'
            }
        ]
    }
    
    # Generate report
    report_generator = ReportGenerator(reports_folder='reports')
    report_path = report_generator.generate_report(
        cleanliness_data,
        evidence_data,
        alert_data,
        location_name="Main Campus - Test Area"
    )
    
    report_generator.print_report_summary(report_path)


# If this file is run directly, test report generator
if __name__ == "__main__":
    test_report_generator()