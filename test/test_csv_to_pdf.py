import unittest
import os
import csv
from unittest.mock import patch, mock_open, MagicMock
from src.csv_to_pdf import CsvToPdf

class TestCsvToPdf(unittest.TestCase):

    def setUp(self):
        self.csv_folder = "test_csv"
        os.makedirs(self.csv_folder, exist_ok=True)
        self.csv_file = os.path.join(self.csv_folder, "test.csv")
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["pdf", "other_column"])
            writer.writerow(["http://example.com/test.pdf", "data1"])
            writer.writerow(["http://example.com/another.pdf", "data2"])
        
        self.converter = CsvToPdf(csv_folder=self.csv_folder)


    def tearDown(self):
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        if os.path.exists(self.csv_folder):
            os.rmdir(self.csv_folder)

    def test_get_last_csv_no_files(self):
        os.remove(self.csv_file)
        last_csv = self.converter.get_last_csv()
        self.assertIsNone(last_csv)

    def test_get_url_from_csv_file_not_found(self):
        urls = self.converter.get_url_from_csv("non_existent_file.csv")
        self.assertEqual(urls, [])

    def test_get_url_from_csv_key_error(self):
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["wrong_header", "other_column"])
            writer.writerow(["http://example.com/test.pdf", "data1"])
        
        urls = self.converter.get_url_from_csv(self.csv_file)
        self.assertEqual(urls, [])

    @patch('src.csv_to_pdf.requests.get')
    def test_download_pdf_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/pdf', 'content-disposition': 'attachment; filename=test.pdf'}
        mock_response.content = b'pdf content'
        mock_get.return_value = mock_response

        with patch('builtins.open', mock_open()) as mock_file:
            output_path = self.converter.download_pdf("http://example.com/test.pdf", "dummy_folder")
            self.assertIsNotNone(output_path)
            mock_file.assert_called_once_with(output_path, 'wb')
            mock_file().write.assert_called_once_with(b'pdf content')

    @patch('src.csv_to_pdf.requests.get')
    def test_download_pdf_request_exception(self, mock_get):
        mock_get.side_effect = Exception("Request failed")
        output_path = self.converter.download_pdf("http://example.com/test.pdf", "dummy_folder")
        self.assertIsNone(output_path)

    @patch('src.csv_to_pdf.CsvToPdf.download_pdf')
    @patch('src.csv_to_pdf.PdfWriter')
    def test_get_merge_pdfs(self, mock_pdf_writer, mock_download_pdf):
        mock_download_pdf.return_value = "dummy.pdf"
        mock_merger = MagicMock()
        mock_pdf_writer.return_value = mock_merger

        urls = ["http://example.com/test.pdf"]
        self.converter.get_merge_pdfs(urls)

        mock_download_pdf.assert_called_once()
        mock_merger.append.assert_called_once_with("dummy.pdf")
        mock_merger.write.assert_called_once_with(self.converter.outputfile)
        mock_merger.close.assert_called_once()

    def test_get_last_csv(self):
        converter = CsvToPdf(csv_folder=self.csv_folder)
        last_csv = converter.get_last_csv()
        self.assertEqual(last_csv, self.csv_file)

    def test_get_url_from_csv(self):
        converter = CsvToPdf()
        urls = converter.get_url_from_csv(self.csv_file)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "http://example.com/test.pdf")
        self.assertEqual(urls[1], "http://example.com/another.pdf")

    def test_get_filename_from_header(self):
        converter = CsvToPdf()
        header_with_filename = {"content-disposition": "attachment; filename=test.pdf"}
        filename = converter._get_filename_from_header(header_with_filename)
        self.assertEqual(filename, "test.pdf")

        header_without_filename = {"content-disposition": "attachment"}
        filename = converter._get_filename_from_header(header_without_filename)
        self.assertIsNone(filename)

        header_without_content_disposition = {}
        filename = converter._get_filename_from_header(header_without_content_disposition)
        self.assertIsNone(filename)

    def test_is_pdf_file(self):
        converter = CsvToPdf()
        pdf_header = {"content-type": "application/pdf"}
        self.assertTrue(converter._is_pdf_file(pdf_header))

        octet_stream_header = {"content-type": "application/octet-stream", "content-disposition": "attachment; filename=test.pdf"}
        self.assertTrue(converter._is_pdf_file(octet_stream_header))

        octet_stream_header_no_pdf = {"content-type": "application/octet-stream", "content-disposition": "attachment; filename=test.txt"}
        self.assertFalse(converter._is_pdf_file(octet_stream_header_no_pdf))
        
        html_header = {"content-type": "text/html"}
        self.assertFalse(converter._is_pdf_file(html_header))

if __name__ == '__main__':
    unittest.main()
