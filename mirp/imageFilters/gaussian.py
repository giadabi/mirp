import numpy as np
import copy

from typing import Union, List
from mirp.imageClass import ImageClass
from mirp.imageFilters.genericFilter import GenericFilter
from mirp.imageFilters.utilities import FilterSet2D, FilterSet3D
from mirp.importSettings import SettingsClass


class GaussianFilter(GenericFilter):

    def __init__(self, settings: SettingsClass, name: str):
        super().__init__(
            settings=settings,
            name=name
        )

        self.sigma = settings.img_transform.gaussian_sigma
        self.sigma_cutoff = settings.img_transform.gaussian_sigma_truncate
        self.mode = settings.img_transform.gaussian_boundary_condition

        # Riesz transformation settings.
        self.riesz_order: Union[None, List[int], List[List[int]]] = None
        self.riesz_steered: bool = False
        self.riesz_sigma: Union[None, float, List[float]] = None
        if settings.img_transform.has_riesz_filter(x=name):
            self.riesz_order = settings.img_transform.riesz_order

            if settings.img_transform.has_steered_riesz_filter(x=name):
                self.riesz_steered = True
                self.riesz_sigma = settings.img_transform.riesz_filter_tensor_sigma

    def generate_object(self):
        # Generator for transformation objects.
        sigma = copy.deepcopy(self.sigma)
        if not isinstance(sigma, list):
            sigma = [sigma]

        riesz_order = copy.deepcopy(self.riesz_order)
        if riesz_order is None:
            riesz_order = [None]
        elif not all(isinstance(riesz_order_set, list) for riesz_order_set in riesz_order):
            riesz_order = [riesz_order]

        riesz_sigma = copy.deepcopy(self.riesz_sigma)
        if not isinstance(riesz_sigma, list):
            riesz_sigma = [riesz_sigma]

        # Iterate over options to yield filter objects with specific settings. A copy of the parent object is made to
        # avoid updating by reference.
        for current_sigma in sigma:
            for current_riesz_order in riesz_order:
                for current_riesz_sigma in riesz_sigma:
                    filter_object = copy.deepcopy(self)
                    filter_object.sigma = current_sigma
                    filter_object.riesz_order = current_riesz_order
                    filter_object.riesz_sigma = current_riesz_sigma

                    yield filter_object

    def transform_deprecated(self, img_obj: ImageClass):
        """
        Transform image by calculating the laplacian of the gaussian second derivatives
        :param img_obj: image object

        :return:
        """

        # Copy base image
        response_map = img_obj.copy(drop_image=True)

        # Set spatial transformation string for transformed object
        response_map.set_spatial_transform("gauss_s" + str(self.sigma))

        # Skip transform in case the input image is missing
        if img_obj.is_missing:
            return response_map

        # Calculate sigma for current image
        vox_sigma = np.divide(
            np.full(shape=3, fill_value=self.sigma),
            img_obj.spacing)

        # Apply filters
        response_map.set_voxel_grid(voxel_grid=self.transform_grid(
            voxel_grid=img_obj.get_voxel_grid(),
            sigma=vox_sigma))

        return response_map

    def transform_grid(self,
                       voxel_grid: np.array,
                       sigma: np.array):
        # Determine the size of the filter
        filter_size = 1 + 2 * np.floor(self.sigma_cutoff * sigma + 0.5)
        filter_size.astype(np.int)

        if self.by_slice:
            # Set the number of dimensions.
            d = 2.0

            # Create the grid coordinates, with [0, 0, 0] in the center.
            y, x = np.mgrid[:filter_size[1], :filter_size[2]]
            y -= (filter_size[1] - 1.0) / 2.0
            x -= (filter_size[2] - 1.0) / 2.0

            # Compute the square of the norm.
            norm_2 = np.power(y, 2.0) + np.power(x, 2.0)

        else:
            # Set the number of dimensions.
            d = 3.0

            # Create the grid coordinates, with [0, 0, 0] in the center.
            z, y, x = np.mgrid[:filter_size[0], :filter_size[1], :filter_size[2]]
            z -= (filter_size[0] - 1.0) / 2.0
            y -= (filter_size[1] - 1.0) / 2.0
            x -= (filter_size[2] - 1.0) / 2.0

            # Compute the square of the norm.
            norm_2 = np.power(z, 2.0) + np.power(y, 2.0) + np.power(x, 2.0)

        # Set a single sigma value.
        sigma = np.max(sigma)

        # Compute the scale factor
        scale_factor = np.power(1.0 / np.sqrt(2.0 * np.pi * sigma ** 2), d)

        # Compute the exponent which determines filter width.
        width_factor = - norm_2 / (2.0 * sigma ** 2.0)

        # Compute the weights of the filter.
        filter_weights = np.multiply(scale_factor, np.exp(width_factor))

        if self.by_slice:
            # Set filter weights and create a filter.
            gauss_filter = FilterSet2D(filter_weights,
                                       riesz_order=self.riesz_order,
                                       riesz_steered=self.riesz_steered,
                                       riesz_sigma=self.riesz_sigma)

            # Convolve laplacian of gaussian filter with the image.
            response_map = gauss_filter.convolve(voxel_grid=voxel_grid,
                                                 mode=self.mode,
                                                 response="real")

        else:
            # Set filter weights and create a filter.
            gauss_filter = FilterSet3D(filter_weights,
                                       riesz_order=self.riesz_order,
                                       riesz_steered=self.riesz_steered,
                                       riesz_sigma=self.riesz_sigma)

            # Convolve laplacian of gaussian filter with the image.
            response_map = gauss_filter.convolve(voxel_grid=voxel_grid,
                                                 mode=self.mode,
                                                 response="real")

        # Compute the convolution
        return response_map
