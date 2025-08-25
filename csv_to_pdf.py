#!/bin/env python3

import csv
from pypdf import PdfReader, PdfWriter
import glob
import logging
import os

logging.basicConfig(
    format="%(asctime)s %(levelname)-4s %(message)s",
    filename="csv_to_pdf.log",
    encoding="utf-8",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_last_csv(directory="."):
    """Returns the rows from a CSV file."""
    try:
        csv_files = glob.glob(os.path.join("csv", "*.csv"))

        if not csv_files:
            logger.warning("No CSV files found in the 'csv' directory.")
            return []

        latest_csv = max(csv_files, key=os.path.getmtime)
        return latest_csv

    except Exception as e:
        logger.error(f"Error reading CSV files: {e}")
        return []


def parse_csv_for_urls(csv_file):
    """Returns the urls from csv file."""
    reader = csv.DictReader(csv_file)
    rows = list(reader)
    urls = []
    for row in rows:
        urls.append(row['pdf'])
    return urls
    
def get_pdf_from_url(urls):
    pass

def merge_pdfs(pdfs):
    pass

def send_output(merged_pdf, sender, receiver):
    pass

def main():
    pass


if __name__ == "__main__":
    main()
