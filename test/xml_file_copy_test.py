import os
import pytest
from mirp.utilities.config_utilities import get_settings_xml, get_data_xml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.ci
def test_copy_settings_xml(tmp_path):
    target_file = os.path.join(tmp_path, "settings.xml")

    # Start with a clean slate.
    if os.path.exists(target_file):
        os.remove(target_file)

    get_settings_xml(target_dir=tmp_path)

    assert os.path.exists(target_file)

    # Clean up.
    os.remove(target_file)


@pytest.mark.ci
def test_copy_data_xml(tmp_path):
    target_file = os.path.join(tmp_path, "data.xml")

    # Start with a clean slate.
    if os.path.exists(target_file):
        os.remove(target_file)

    get_data_xml(target_dir=tmp_path)

    assert os.path.exists(target_file)

    # Clean up.
    os.remove(target_file)
