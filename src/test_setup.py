# test_setup.py
# This script tests if all libraries are installed correctly

import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

print("✅ OpenCV version:", cv2.__version__)
print("✅ NumPy version:", np.__version__)
print("✅ PIL (Pillow) imported successfully")
print("✅ Ultralytics (YOLO) imported successfully")
print("\n🎉 All libraries installed correctly!")
print("Your environment is ready for development.")