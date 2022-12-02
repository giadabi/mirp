from typing import Union, Dict

import pandas as pd
from pydicom import dcmread
from warnings import warn

from mirp.importData.importImageFile import ImageFile
from mirp.importData.utilities import supported_modalities
from mirp.imageMetaData import get_pydicom_meta_tag


class ImageDicomFile(ImageFile):
    def __init__(self,
                 file_path: str,
                 file_type: str,
                 sample_name: Union[None, str] = None,
                 suggested_sample_name: Union[None, str, dict[str, str, str]] = None,
                 image_name: Union[None, str] = None,
                 modality: Union[None, str] = None):

        super().__init__(file_path=file_path,
                         sample_name=sample_name,
                         suggested_sample_name=suggested_sample_name,
                         image_name=image_name,
                         modality=modality,
                         file_type=file_type)

        # These are set using the 'complete' method.
        self.frame_of_reference_uid = None
        self.sop_instance_uid = None

    def check(self, raise_error=False):

        # Perform general checks.
        if not super().check(raise_error=raise_error):
            return False

        # Read DICOM file.
        dcm = dcmread(self.file_path,
                      stop_before_pixels=True,
                      force=True)

        # Check that modality is matching.
        dicom_modality = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0008, 0x0060), tag_type="str")
        support_modalities = supported_modalities(self.modality)
        if dicom_modality.lower() not in support_modalities:
            if raise_error:
                raise ValueError(f"The current DICOM file {self.file_path} does not have the expected modality. "
                                 f"Found: {dicom_modality.lower()}. Expected: {', '.join(support_modalities)}")

            return False

        return True

    def complete(self):

        # Read DICOM file.
        dcm = dcmread(self.file_path,
                      stop_before_pixels=True,
                      force=True)

        # Attempt to set the modality attribute.
        if self.modality is None:
            self.modality = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0008, 0x0060), tag_type="str")

        if self.modality is None:
            warn(f"Could not ascertain the modality from the DICOM file ({self.file_path}).",
                 UserWarning)

            self.modality = "generic"
        else:
            self.modality = self.modality.lower()

        # Set SOP instance UID.
        self.sop_instance_uid = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0008, 0x0018), tag_type="str")

        # Set Frame of Reference UID (if any)
        self.frame_of_reference_uid = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0020, 0x0052), tag_type="str")

        # Set patient name if its not known. First try the patient ID attribute, and subsequently patient name.
        if self.sample_name is None:
            self.sample_name = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0010, 0x0020), tag_type="str")

        if self.sample_name is None:
            temporary_name = get_pydicom_meta_tag(dcm_seq=dcm, tag=(0x0010, 0x0010), tag_type="str")

            if temporary_name is not None:
                # Strip ^ from temporary name.
                self.sample_name = temporary_name.strip("^_ ")

    def get_identifiers(self, style):
        if style == "basic":
            return pd.DataFrame.from_dict(dict({"modality": [self.modality],
                                                "sample_name": [self.sample_name]}))

        elif style == "extended":
            return pd.DataFrame.from_dict(dict({"modality": [self.modality],
                                                "file_type": [self.file_type],
                                                "sample_name": [self.sample_name],
                                                "sop_instance_uid": [self.sop_instance_uid]}))

        else:
            raise ValueError(f"The style parameter should be either 'basic' or 'extended'. Found: {style}")
