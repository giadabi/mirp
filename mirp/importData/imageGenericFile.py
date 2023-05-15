import os
import os.path

import pandas as pd

from typing import Union
from mirp.importData.utilities import supported_file_types, match_file_name, bare_file_name


class ImageFile:

    def __init__(
            self,
            file_path: Union[None, str] = None,
            dir_path: Union[None, str] = None,
            sample_name: Union[None, str] = None,
            file_name: Union[None, str] = None,
            image_name: Union[None, str] = None,
            image_modality: Union[None, str] = None,
            image_file_type: Union[None, str] = None,
            **kwargs):

        # Sanity check.
        if isinstance(sample_name, list):
            raise ValueError("The sample_name argument should be None or a string.")

        self.file_path: Union[None, str] = file_path
        self.sample_name: Union[None, str] = sample_name
        self.image_name: Union[None, str] = image_name
        self.modality: Union[None, str] = image_modality
        self.file_type: Union[None, str] = image_file_type

        # Attempt to set the file name, if this is not externally provided.
        if isinstance(file_path, str) and file_name is None:
            file_name = os.path.basename(file_path)

            file_extension = None
            for current_file_extension in supported_file_types(self.file_type):
                if file_name.endswith(current_file_extension):
                    file_extension = current_file_extension
                    break

            if file_extension is not None:
                file_name = file_name.replace(file_extension, "")

            file_name = file_name.strip(" _^*")

        # Attempt to set the directory path, if this is not externally provided.
        if isinstance(file_path, str) and dir_path is None:
            dir_path = os.path.dirname(file_path)

        self.file_name: Union[None, str] = file_name
        self.dir_path: Union[None, str] = dir_path

    def set_sample_name(
            self,
            sample_name: str):

        self.sample_name = sample_name

    def get_sample_name(self):
        if self.sample_name is None:
            return "unset_sample_name__"

        return self.sample_name

    def get_file_name(self):
        if self.file_name is None:
            return "unset_file_name__"

        return self.file_name

    def get_dir_path(self):
        if self.dir_path is None:
            return "unset_dir_path__"

        return self.dir_path

    def create(self):
        # Import locally to avoid potential circular references.
        from mirp.importData.imageDicomFile import ImageDicomFile
        from mirp.importData.imageNiftiFile import ImageNiftiFile
        from mirp.importData.imageNrrdFile import ImageNrrdFile
        from mirp.importData.imageNumpyFile import ImageNumpyFile

        file_extensions = supported_file_types(file_type=self.file_type)

        if any(self.file_path.lower().endswith(ii) for ii in file_extensions) and\
                any(self.file_path.lower().endswith(ii) for ii in supported_file_types("dicom")):

            # Create DICOM-specific file.
            image_file = ImageDicomFile(
                file_path=self.file_path,
                dir_path=self.dir_path,
                sample_name=self.sample_name,
                file_name=self.file_name,
                image_name=self.image_name,
                modality=self.modality,
                image_file_type="dicom")

        elif any(self.file_path.lower().endswith(ii) for ii in file_extensions) and\
                any(self.file_path.lower().endswith(ii) for ii in supported_file_types("nifti")):

            # Create Nifti file.
            image_file = ImageNiftiFile(
                file_path=self.file_path,
                dir_path=self.dir_path,
                sample_name=self.sample_name,
                file_name=self.file_name,
                image_name=self.image_name,
                modality=self.modality,
                image_file_type="nifti")

        elif any(self.file_path.lower().endswith(ii) for ii in file_extensions) and\
                any(self.file_path.lower().endswith(ii) for ii in supported_file_types("nrrd")):

            # Create NRRD file.
            image_file = ImageNrrdFile(
                file_path=self.file_path,
                dir_path=self.dir_path,
                sample_name=self.sample_name,
                file_name=self.file_name,
                image_name=self.image_name,
                modality=self.modality,
                image_file_type="nrrd")

        elif any(self.file_path.lower().endswith(ii) for ii in file_extensions) and\
                any(self.file_path.lower().endswith(ii) for ii in supported_file_types("numpy")):

            # Create Numpy file.
            image_file = ImageNumpyFile(
                file_path=self.file_path,
                dir_path=self.dir_path,
                sample_name=self.sample_name,
                file_name=self.file_name,
                image_name=self.image_name,
                modality=self.modality,
                image_file_type="numpy")

        else:
            raise NotImplementedError(f"The provided image type is not implemented: {self.file_type}")

        return image_file

    def check(self, raise_error=False):
        # Check if file_path is set. Otherwise, none of the generic checks below can be used.
        if self.file_path is None:
            return True

        # Dispatch to subclass based on file_path.
        allowed_file_extensions = supported_file_types(self.file_type)

        # Check that the file type is correct.
        if not self.file_path.lower().endswith(tuple(allowed_file_extensions)):
            if raise_error:
                raise ValueError(
                    f"The file type does not correspond to a known, implemented image type: {self.file_type}.")

            return False

        # Check that the file exists.
        if not os.path.exists(self.file_path):
            if raise_error:
                raise FileNotFoundError(
                    f"The image file could not be found at the expected location: {self.file_path}")

            return False

        # Check that the file name contains image_name.
        if self.image_name is not None:
            if not match_file_name(self.file_path, pattern=self.image_name, file_extension=allowed_file_extensions):
                if raise_error:
                    raise ValueError(
                        f"The file name of the image file {os.path.basename(self.file_path)} does not match "
                        f"the expected pattern: {self.image_name}")

            return False

        # Check that image file contains a sample name, if multiple sample names are present. To assess the filename,
        # we first strip the extension. Optionally we split the filename on the image name pattern, reducing the
        # filename into parts that should contain the sample name.
        if isinstance(self.sample_name, list) and len(self.sample_name) > 1:
            file_name = bare_file_name(x=self.file_name, file_extension=allowed_file_extensions)
            if self.image_name is not None:
                image_id_name = self.image_name
                if not isinstance(self.image_name, list):
                    image_id_name = [image_id_name]

                # Find the id that is present in the filename.
                matching_image_id = None
                for current_image_id_name in image_id_name:
                    if current_image_id_name in file_name:
                        matching_image_id = current_image_id_name
                        break

                if matching_image_id is not None:
                    # Handle wildcards in the image id.
                    matching_image_id.replace("?", "*")
                    matching_image_id = matching_image_id.split("*")
                    matching_image_id = [x for x in matching_image_id if x != ""]

                    if len(matching_image_id) == 0:
                        file_name_parts = [file_name]
                    else:
                        # Find the parts of the file name that do not contain the image identifier.
                        blocked_start = file_name.find(matching_image_id[0])
                        blocked_end = file_name.find(matching_image_id[-1]) + len(matching_image_id[-1])
                        file_name_parts = [""]
                        if blocked_start > 0:
                            file_name_parts.append(file_name[0:blocked_start])

                        if blocked_end < len(file_name):
                            file_name_parts.append(file_name[blocked_end:len(file_name)])
                else:
                    file_name_parts = [file_name]

            else:
                file_name_parts = [file_name]

            # Check if any sample name is present.
            contains_sample_name = [
                any([x in current_file_name_part for x in self.sample_name])
                for current_file_name_part in file_name_parts
            ]

            if not contains_sample_name:
                if raise_error:
                    raise ValueError(
                        f"The file name of the image file {os.path.basename(self.file_path)} does not contain "
                        f"any of the expected patterns: {', '.join(self.sample_name)}")
                else:
                    return False

        return True

    def get_identifiers(self):

        return pd.DataFrame.from_dict(dict({
            "modality": [self.modality],
            "file_type": [self.file_type],
            "sample_name": [self.get_sample_name()],
            "file_name": [self.get_file_name()],
            "dir_path": [self.get_dir_path()]}))

    def complete(self):
        # Set modality
        if self.modality is None:
            self.modality = "generic"

        # Set sample name.

