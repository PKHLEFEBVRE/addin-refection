import csv
import logging
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_lines_from_excel_file(path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads an Excel file and returns a list of dictionaries (one per row)."""
    try:
        df = pd.read_excel(path, sheet_name=sheet_name) if sheet_name else pd.read_excel(path)
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Failed to read Excel file at {path}: {str(e)}")
        return []

def get_lines_from_csv(path: str, delimiter: str = ';') -> List[Dict[str, Any]]:
    """Reads a CSV file and returns a list of dictionaries (one per row)."""
    try:
        df = pd.read_csv(path, sep=delimiter, encoding='utf-8')
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Failed to read CSV file at {path}: {str(e)}")
        return []

def parse_xml_file(path: str) -> Optional[ET.Element]:
    try:
        return ET.parse(path).getroot()
    except Exception as e:
        logger.error(f"Failed to parse XML file at {path}: {str(e)}")
        return None

def extract_zip(zip_path: str, extract_to: str) -> bool:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        logger.error(f"Failed to extract ZIP file at {zip_path}: {str(e)}")
        return False
