import cv2
import numpy as np
import pandas as pd
from .core_ocr import OCREngine

class TableExtractor:
    def __init__(self, ocr_engine):
        self.ocr = ocr_engine

    def extract_table(self, image_path):
        """
        Attempt to extract a table from the image.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found")

        # 1. Convert to grayscale and process
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        thresh = 255 - thresh # Invert colors

        # 2. Detect horizontal and vertical lines
        rows = gray.shape[0]
        vertical_size = rows // 30
        vertical_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
        vertical = cv2.erode(thresh, vertical_structure)
        vertical = cv2.dilate(vertical, vertical_structure)

        cols = gray.shape[1]
        horizontal_size = cols // 30
        horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
        horizontal = cv2.erode(thresh, horizontal_structure)
        horizontal = cv2.dilate(horizontal, horizontal_structure)

        # 3. Combine lines to get the grid
        grid = cv2.add(horizontal, vertical)
        
        # 4. Find cells (Contours)
        contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter out very small contours
        cells = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 20 and h > 10: # Ignore noise
                cells.append((x, y, w, h))

        # 5. Sort cells (Top-to-bottom, then Left-to-right)
        # This sort is simple and might need improvement for complex tables
        cells.sort(key=lambda b: (b[1] // 10, b[0])) # Cluster by rows approximately

        data = []
        current_row_y = -1
        row_data = []

        # Read each cell
        for (x, y, w, h) in cells:
            # Crop cell
            roi = img[y:y+h, x:x+w]
            
            # Read text inside cell
            results = self.ocr.read_image_from_array(roi, detail=0)
            text = " ".join(results).strip()
            
            # Simple logic to determine rows (if Y changes significantly, start new row)
            if current_row_y == -1:
                current_row_y = y
            
            if abs(y - current_row_y) > 20:
                data.append(row_data)
                row_data = []
                current_row_y = y
            
            row_data.append(text)
        
        if row_data:
            data.append(row_data)

        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df
