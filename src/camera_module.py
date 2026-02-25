# camera_module.py
# This module handles camera input and video capture

import cv2
import sys

class CameraModule:
    """
    A class to handle camera operations
    """
    
    def __init__(self, camera_index=0):
        """
        Initialize the camera
        
        Args:
            camera_index: Which camera to use (0 = default webcam, 1 = external camera)
        """
        print("🎥 Initializing camera...")
        self.camera = cv2.VideoCapture(camera_index)
        
        # Check if camera opened successfully
        if not self.camera.isOpened():
            print("❌ ERROR: Could not open camera!")
            print("Make sure your webcam is connected and not being used by another app.")
            sys.exit(1)
        
        # Set camera resolution (width x height)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("✅ Camera initialized successfully!")
    
    def read_frame(self):
        """
        Capture one frame from the camera
        
        Returns:
            success: True if frame captured, False otherwise
            frame: The captured image (numpy array)
        """
        success, frame = self.camera.read()
        return success, frame
    
    def release(self):
        """
        Release the camera when we're done
        """
        print("📴 Releasing camera...")
        self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Camera released successfully!")


def test_camera():
    """
    Test function to check if camera works
    """
    print("\n" + "="*50)
    print("TESTING CAMERA MODULE")
    print("="*50 + "\n")
    
    # Create camera object
    cam = CameraModule(camera_index=0)
    
    print("\n📹 Starting live camera feed...")
    print("Press 'q' to quit\n")
    
    # Counter for frames
    frame_count = 0
    
    while True:
        # Read one frame
        success, frame = cam.read_frame()
        
        if not success:
            print("❌ Failed to read frame")
            break
        
        # Increment frame counter
        frame_count += 1
        
        # Add text to frame showing frame number
        cv2.putText(
            frame, 
            f"Frame: {frame_count}", 
            (10, 30),  # Position (x, y)
            cv2.FONT_HERSHEY_SIMPLEX,  # Font style
            1,  # Font size
            (0, 255, 0),  # Color (Green in BGR)
            2  # Thickness
        )
        
        # Add instructions text
        cv2.putText(
            frame,
            "Press 'q' to quit",
            (10, 460),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),  # Yellow
            2
        )
        
        # Show the frame in a window
        cv2.imshow("Smart Campus - Camera Test", frame)
        
        # Wait 1 millisecond and check if 'q' key is pressed
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print(f"\n✅ Total frames captured: {frame_count}")
            break
    
    # Clean up
    cam.release()
    print("\n" + "="*50)
    print("CAMERA TEST COMPLETED")
    print("="*50)


# If this file is run directly, test the camera
if __name__ == "__main__":
    test_camera()