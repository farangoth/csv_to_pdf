#!/bin/env python3

import csv
import glob
import logging
import os
import re
import tempfile

import requests
from pypdf import PdfWriter
from requests.exceptions import HTTPError

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
            return None

        latest_csv = max(csv_files, key=os.path.getmtime)
        logger.info(f"Found csv file: {latest_csv}")
        return latest_csv

    except Exception as e:
        logger.error(f"Error reading CSV files: {e}")
        return None


def parse_csv_for_urls(csv_file):
    """Returns the urls from csv file."""
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        urls = []
        for row in reader:
            logger.info(f"found url: {row['pdf']}")
            urls.append(row["pdf"])
    return urls


def get_headers_from_response(response):
    """Returns headers using requests."""
    try:
        header = response.headers
        logger.info(header)
        return header
    except HTTPError as error:
        logger.error(f"{error}")
        return None


def is_pdf_file(header):
    """Check if the content at url is a pdf file."""
    if "application/pdf" in header["content-type"]:
        return True
    if "application/octet-stream" in header["content-type"]:
        filename = get_filename_from_header(header["content-disposition"])
        return filename.lower().endswith(".pdf")
    return False


def get_filename_from_header(content_disposition):
    """Checks 'content-disposition' for a filename."""
    filename = re.findall("filename=(.+)", content_disposition)
    if len(filename) == 0:
        return None
    return filename[0]


def get_pdf_from_url(url, dest_folder, filename=None):
    """Downloads the pdf file from url."""
    try:
        response = requests.get(url, allow_redirects=True)
        header = get_headers_from_response(response)
        if is_pdf_file(header):
            if filename is None:
                filename = get_filename_from_header(header["content-disposition"])
            destination = os.path.join(dest_folder, filename)
            logger.info(f"downloading {destination} from {url}")
            with open(destination, "wb") as file:
                file.write(response.content)
        else:
            logger.warning(f"no pdf file at {url}")
    except HTTPError as error:
        logger.error(f"Error while opening {url}: {error}")


def download_merge_pdfs(urls):
    """Get all the pdfs and merge them into one file."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        merger = PdfWriter()
        output_name = "output.pdf"
        index = 0
        for url in urls:
            index += 1
            filename = "giftcard" + str(index) + ".pdf"
            get_pdf_from_url(url, tmpdirname, filename)
            merger.append(os.path.join(tmpdirname, filename))
            logger.info(f"add {filename} to {output_name}")
        merger.write(output_name)
        merger.close()


def send_output(merged_pdf, sender, receiver):
    pass


def main():
    csv_file = get_last_csv()
    urls = parse_csv_for_urls(csv_file)
    download_merge_pdfs(urls) 


if __name__ == "__main__":
    main()
