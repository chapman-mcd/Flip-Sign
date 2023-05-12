from flip_sign.helpers import sha256_with_default
from pathlib import Path
from flip_sign.assets import root_dir

test_files = [
    Path(root_dir + "/../tests/helpers/test_assets/signscape_1.png"),
    Path(root_dir + "/../tests/helpers/test_assets/rickroll.jpeg"),
    Path(root_dir + "/../tests/helpers/test_assets/fake_file.lol")
]


answers = [
    'e35af94b8d2b0e87fc94c8d18c6a4d433507146d9f1202206b0a6b5ef8865599',
    'cd026882b910d1306ed26390d4a5e5b5e8b4ffe1856b0c30cb14637c34f0347d',
    "file does not exist lol"
]


def test_sha256_default():
    for file, answer in zip(test_files, answers):
        assert sha256_with_default(file) == answer
