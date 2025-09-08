import cv2
import numpy as np
from PIL import Image
import streamlit as st

class VisualDetector:
    def detect_visual_elements(self, image: Image.Image) -> bool:
        """Detect if image contains diagrams, tables, or charts"""
        try:
            # Convert to OpenCV format
            cv_image = np.array(image.convert('RGB'))
            cv_image = cv_image[:, :, ::-1].copy()  # RGB to BGR
            
            # Simple detection using edge detection and contours
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Count contours that might indicate visual elements
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # If we have many contours or large ones, likely a visual element
            large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]
            return len(large_contours) > 5
            
        except Exception as e:
            st.warning(f"Visual detection error: {e}")
            return False