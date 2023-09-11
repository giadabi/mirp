from typing import Union, Optional, List


def extract_mask_labels(
        mask=None,
        sample_name: Union[None, str, List[str]] = None,
        mask_name: Union[None, str, List[str]] = None,
        mask_file_type: Optional[str] = None,
        mask_modality: Union[None, str, List[str]] = None,
        mask_sub_folder: Optional[str] = None,
        stack_masks: str = "auto",
        write_file: bool = False,
        write_dir: Optional[str] = None,
        **kwargs
):
    """
    Extract labels present in one or more masks.

    Parameters
    ----------
    mask: Any
        A path to a mask file, a path to a directory containing mask files, a path to a config_data.xml
        file, a path to a csv file containing references to mask files, a pandas.DataFrame containing references to
        mask files, or a numpy.ndarray.

    sample_name: str or list of str, optional, default: None
        Name of expected sample names. This is used to select specific mask files. If None, no mask files are filtered
         based on the corresponding sample name (if known).

    mask_name: str, optional, default: None
        Pattern to match mask files against. The matches are exact. Use wildcard symbols ("*") to match varying
        structures. The sample name (if part of the file name) can also be specified using "#". For example,
        mask_name = '#_*_mask' would find John_Doe in John_Doe_CT_mask.nii or John_Doe_001_mask.nii. File extensions
        do not need to be specified. If None, file names are not used for filtering files and setting sample names.

    mask_file_type: {"dicom", "nifti", "nrrd", "numpy", "itk"}, optional, default: None
        The type of file that is expected. If None, the file type is not used for filtering files.
        "itk" comprises "nifti" and "nrrd" file types.

    mask_modality: {"rtstruct", "seg", "generic_mask"}, optional, default: None
        The type of modality that is expected. If None, modality is not used for filtering files.
        Note that only DICOM files contain metadata concerning modality. Options: "rtstruct", "seg" or "generic_mask".
        Masks from non-DICOM files are considered to be "generic_mask".

    mask_sub_folder: str, optional, default: None
        Fixed directory substructure where mask files are located. If None, this directory substructure is not used for
        filtering files.

    stack_masks: {"auto", "yes", "no"}, optional, default: "auto"
        One of auto, yes or no. If mask files in the same directory cannot be assigned to
        different samples, and are 2D (slices) of the same size, they might belong to the same 3D mask stack. "auto"
        will stack 2D numpy arrays, but not other file types. "yes" will stack all files that contain 2D images,
        that have the same dimensions, orientation and spacing, except for DICOM files. "no" will not stack any files.
        DICOM files ignore this argument, because their stacking can be determined from metadata.

    write_file: bool, optional, default: False
        Determines whether the labels should be written to

    Returns
    -------
    list of MaskFile
        The functions returns a list of MaskFile objects, if any were found with the specified filters.

    """
    from mirp.importData.importMask import import_mask

    mask_list = import_mask(
        mask=mask,
        sample_name=sample_name,
        mask_name=mask_name,
        mask_file_type=mask_file_type,
        mask_modality=mask_modality,
        mask_sub_folder=mask_sub_folder,
        stack_masks=stack_masks
    )