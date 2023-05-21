from flip_sign.message_generation import GoogleDriveImageMessageFactory, ImageMessage
from pathlib import Path
from unittest.mock import patch, MagicMock
from flip_sign.assets import root_dir, keys
from tests.helpers.draw_text_test import image_equal
from flip_sign.helpers import sha256_with_default
import json

cache_dir = root_dir + "/cache/google_drive_images/"

file_names = ['Henry_Signscape_1_-_Title_H.png',
              'PupuMeleca_PupuShishi_Unk_CarronaRua_Rua.png',
              'Africa_SouthAmerica_Untitled_FernandodeNoronha_MatoGrosso.png',
              'test_random_portuguese.png',
              'test_avett_datdot.png',
              'Nyan_Cat_Signscape.png',
              'Henry_Signscape_3_-_A_Rio_de_Janeiro_Bop_Meleca.png',
              'Henry_Signscape_2_-_Title_A_Magin_Margret_Basement_House.png',
              'Rio_V1.png']

answers = [ImageMessage(image=Path(cache_dir + file), frequency=1.0) for file in file_names]


def assert_image_message_equal(first_message: ImageMessage, second_message: ImageMessage):
    """
    Asserts two image messages are equal, for the purposes of this test.  Checks if the image is identical.

    :param first_message: (ImageMessage) the left message
    :param second_message: (ImageMessage) the right message
    :return: None
    """

    assert image_equal(first_message.get_image(), second_message.get_image())


def test_multi_page_results():
    with open(root_dir + "/../tests/message_generation/test_assets/google_drive_responses_multi_page.json") as f:
        results = json.load(f)

    with patch('flip_sign.message_generation.build') as build_mock:
        with patch('flip_sign.message_generation.hlp.download_file_google_drive') as download_mock:
            build_mock.return_value.files.return_value.list.return_value.execute.return_value.get.return_value = \
                results[0]

            next_mocks = []
            for result in results[1:]:
                next_mock = MagicMock()
                next_mock.execute.return_value.get.return_value = result
                next_mocks.append(next_mock)
            next_mocks.append(None)

            build_mock.return_value.files.return_value.list_next.side_effect = next_mocks

            factory = GoogleDriveImageMessageFactory(keys['GoogleDriveFolder'])

            outputs = factory.generate_messages()

            assert len(outputs) == len(answers)
            for i, (output, answer) in enumerate(zip(outputs, answers)):
                assert_image_message_equal(output, answer)

            download_mock.assert_not_called()


def test_single_page_results():
    with open(root_dir + "/../tests/message_generation/test_assets/google_drive_responses_1_page.json") as f:
        results = json.load(f)

    with patch('flip_sign.message_generation.build') as build_mock:
        with patch('flip_sign.message_generation.hlp.download_file_google_drive') as download_mock:
            build_mock.return_value.files.return_value.list.return_value.execute.return_value.get.return_value = results

            next_mocks = [None, None]

            build_mock.return_value.files.return_value.list_next.side_effect = next_mocks

            factory = GoogleDriveImageMessageFactory(keys['GoogleDriveFolder'])

            outputs = factory.generate_messages()

            assert len(outputs) == len(answers)
            for output, answer in zip(outputs, answers):
                assert_image_message_equal(output, answer)

            download_mock.assert_not_called()


checksums = [sha256_with_default(Path(cache_dir + file)) for file in file_names]
checksums[4] = "different checksum lol"


def test_download_changed_file():
    with open(root_dir + "/../tests/message_generation/test_assets/google_drive_responses_multi_page.json") as f:
        results = json.load(f)

    with patch('flip_sign.message_generation.build') as build_mock:
        with patch('flip_sign.message_generation.hlp.download_file_google_drive') as download_mock:
            with patch('flip_sign.message_generation.hlp.sha256_with_default') as checksum_mock:
                checksum_mock.side_effect = checksums
                build_mock.return_value.files.return_value.list.return_value.execute.return_value.get.return_value = \
                    results[0]

                next_mocks = []
                for result in results[1:]:
                    next_mock = MagicMock()
                    next_mock.execute.return_value.get.return_value = result
                    next_mocks.append(next_mock)
                next_mocks.append(None)

                build_mock.return_value.files.return_value.list_next.side_effect = next_mocks

                factory = GoogleDriveImageMessageFactory(keys['GoogleDriveFolder'])

                outputs = factory.generate_messages()

                assert len(outputs) == len(answers)
                for i, (output, answer) in enumerate(zip(outputs, answers)):
                    assert_image_message_equal(output, answer)

                download_mock.assert_called_once()
                assert download_mock.call_args.kwargs['file_id'] == '1tac52DqQ3joNT4OBvhy4Z76V2txjb-to'
                assert download_mock.call_args.kwargs['out_path'] == Path(cache_dir + file_names[4])
