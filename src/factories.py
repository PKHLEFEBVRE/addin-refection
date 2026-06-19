import csv
import logging
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class CommunFactory:
    @staticmethod
    def is_array_empty(arr: Any) -> bool:
        if arr is None:
            return True
        if isinstance(arr, list) and len(arr) == 0:
            return True
        if hasattr(arr, 'size') and arr.size == 0:
            return True
        return False

class ExcelFactory:
    @staticmethod
    def get_lines_from_excel_file(path: str, sheet_name: Optional[str] = None, header: bool = True) -> List[List[Any]]:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name) if sheet_name else pd.read_excel(path)
            # Fill NaNs with empty string or similar if desired, though pandas defaults to None/NaN
            df = df.fillna("")
            # Include headers as first row if requested
            if header:
                return [df.columns.tolist()] + df.values.tolist()
            else:
                return df.values.tolist()
        except Exception as e:
            logger.error(f"Failed to read Excel file at {path}: {str(e)}")
            return []

class CsvFactory:
    @staticmethod
    def get_lines_from_csv(path: str, delimiter: str = ';') -> List[List[str]]:
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=delimiter)
                return [row for row in reader]
        except Exception as e:
            logger.error(f"Failed to read CSV file at {path}: {str(e)}")
            return []

class XmlFactory:
    @staticmethod
    def parse_xml_file(path: str) -> Optional[ET.Element]:
        try:
            tree = ET.parse(path)
            return tree.getroot()
        except Exception as e:
            logger.error(f"Failed to parse XML file at {path}: {str(e)}")
            return None

class ZipFactory:
    @staticmethod
    def extract_zip(zip_path: str, extract_to: str) -> bool:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            logger.error(f"Failed to extract ZIP file at {zip_path}: {str(e)}")
            return False
