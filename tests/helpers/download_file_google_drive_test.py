from flip_sign.helpers import download_file_google_drive
from unittest.mock import patch, MagicMock
from pathlib import Path
from googleapiclient.http import MediaDownloadProgress


def test_download_file():
    with patch('flip_sign.helpers.MediaIoBaseDownload') as download_mock:
        with patch('flip_sign.helpers.io') as io_mock:
            test_progress = MediaDownloadProgress(5, 10)
            build_mock = MagicMock()
            build_mock.files.return_value.get_media.return_value = "dummy request object"

            # mock so download finishes in 1 chunk
            download_mock.return_value.next_chunk.return_value = (test_progress, True)
            io_mock.FileIO.return_value = "dummy file handler"

            download_file_google_drive(file_id="yyz", out_path="/blurgh/test.png", drive_service=build_mock)

            # confirm proper filename used in download
            io_mock.FileIO.assert_called_with("/blurgh/test.png", mode='wb')

            build_mock.files.return_value.get_media.assert_called_once_with(fileId="yyz")

            # confirm request object properly passed in
            download_mock.assert_called_once_with(fd="dummy file handler", request='dummy request object')


def test_download_file_path():
    with patch('flip_sign.helpers.MediaIoBaseDownload') as download_mock:
        with patch('flip_sign.helpers.io') as io_mock:
            test_progress = MediaDownloadProgress(5, 10)
            build_mock = MagicMock()
            build_mock.files.return_value.get_media.return_value = "dummy request object"

            # mock so download finishes in 1 chunk
            download_mock.return_value.next_chunk.return_value = (test_progress, True)
            io_mock.FileIO.return_value = "dummy file handler"

            download_file_google_drive(file_id="yyz", out_path=Path("/blurgh/test.png"), drive_service=build_mock)

            # confirm proper filename used in download
            io_mock.FileIO.assert_called_with("/blurgh/test.png", mode='wb')

            build_mock.files.return_value.get_media.assert_called_once_with(fileId="yyz")

            # confirm request object properly passed in
            download_mock.assert_called_once_with(fd="dummy file handler", request='dummy request object')
