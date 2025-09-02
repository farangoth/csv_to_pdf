#!/bin/env python3

import csv
import glob
import logging
import os
import re
import tempfile

import requests
from pypdf import PdfWriter

from decorators import progress_bar

logging.basicConfig(
    format="%(asctime)s %(levelname)-4s %(message)s",
    filename="csv_to_pdf.log",
    encoding="utf-8",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# parser = argparse.ArgumentParser(
#     prog="csv_to_pdf",
#     description="Downloads PDFs from URLs in a CSV file and merge them into a single PDF.",
# )
# parser.add_argument(
#     "input",
#     nargs="?",
#     help="csv file with the url to download. Must be in the 'pdf' column",
# )
# parser.add_argument("-o", "--output", help="name of the pdf file to export")


class CsvToPdf:
    """A class to handle the downloading and merging of pdf."""

    def __init__(self, csv_folder="csv", keyword="pdf", outputfile="output.pdf"):
        self.csv_folder = csv_folder
        self.keyword = keyword
        self.outputfile = outputfile

    def __str__(self):
        output = self.outputfile
        return f"csv --> {output}"

    def get_last_csv(self):
        """Get the last modified csv."""
        csv_files = glob.glob(os.path.join(self.csv_folder, "*.csv"))
        if not csv_files:
            return None

        last_csv = max(csv_files, key=os.path.getmtime)
        return last_csv

    def get_url_from_csv(self, csv_file):
        """Returns the list of urls from a column of CSV file. The column is selected using a keyword."""
        try:
            with open(csv_file, encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                return [row[self.keyword] for row in reader]
        except FileNotFoundError as error:
            logger.error(f"no {csv_file} in {self.csv_folder}: {error}")
            return []
        except KeyError as error:
            logger.error(f"no {self.keyword} in {csv_file}: {error}")
            return []

    def _get_filename_from_header(self, header):
        """Retuns the filename from content-disposition of an header."""
        content_disposition = header.get("content-disposition")
        if not content_disposition:
            return None
        filename_match = re.search("filename=(.+)", content_disposition)
        if not filename_match:
            return None
        return filename_match.group(1).strip("'\"")
        

    def _is_pdf_file(self, header):
        """Check if the file at url is a pdf file"""
        content_type = header.get("content-type", "")
        if "application/pdf" in content_type:
            return True
        if "application/octet-stream" in content_type:
            filename = self._get_filename_from_header(header)
            return filename.lower().endswith(".pdf") if filename else False

    def download_pdf(self, url, output_folder):
        """Get pdf files from url."""

        try:
            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()

            header = response.headers
            if self._is_pdf_file(header):
                filename = self._get_filename_from_header(header) or f"download_{url}.pdf"
                output = os.path.join(output_folder, filename)
                logger.info(f"downloading {filename} from {url}")
                with open(output, "wb") as file:
                    file.write(response.content)
                    return output
            else:
                logger.warning(f"no pdf file at {url}")
                return None
        except requests.RequestException as error:
            logger.exception(f"error on {url}: {error}")
    
    @progress_bar
    def get_merge_pdfs(self, urls):
        """Download all pdf in temp dir and merge them to output."""
        logger.info(f"{self} is downloading")
        merger = PdfWriter()
        with tempfile.TemporaryDirectory() as tmpdir:
            step = 0
            for url in urls:
                step += 1
                pdffile = self.download_pdf(url, tmpdir)
                try:
                    merger.append(pdffile)
                    logger.info(f"{pdffile} added to {self.outputfile}")
                except Exception as e:
                    logger.error(f"error while adding {pdffile}: {e}")
                yield (step / len(urls))
            if merger.pages:
                merger.write(self.outputfile)
                logger.info(f"{self.outputfile} created")
            else:
                logger.warning("no PDF  has been added.")
            merger.close()
        logger.info("-- END MERGING --")


def main():
    csvtopdf = CsvToPdf()
    csv_file = csvtopdf.get_last_csv()
    urls = csvtopdf.get_url_from_csv(csv_file)
    print(f"{csv_file} ({len(urls)} pdf) --> {csvtopdf.outputfile}")
    logger.info(f"{csv_file} ({len(urls)} pdf) --> {csvtopdf.outputfile}")
    csvtopdf.get_merge_pdfs(urls)


if __name__ == "__main__":
    main()
