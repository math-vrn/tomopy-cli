from unittest import mock, TestCase, expectedFailure, skip

import numpy as np
import tomopy

from tomopy_cli.prep import remove_stripe, minus_log, flat_correction, cap_sinogram_values


def make_params():
    params = mock.MagicMock()
    return params


class PrepTests(TestCase):
    '''Class to test tomopy_cli/prep.py
    '''
    def test_minus_log(self):
        params = mock.MagicMock()
        params.minus_log = False
        data = np.linspace(0.05, 1.0, 20)
        np.testing.assert_array_equal(minus_log(data, params), data)
        params.minus_log = True
        ext_length_data = minus_log(data, params)
        self.assertAlmostEqual(ext_length_data[-1], 0.0)
        self.assertAlmostEqual(ext_length_data[9], 0.693147181)

    def test_flat_normalization(self):
        params = make_params()
        params.flat_correction_method = 'standard'
        params.bright_exp_ratio = 1.0
        params.normalization_cutoff = 1.1
        proj = np.array([10., 5.0, 10., 5.])
        flat = np.array([10., 10., 10., 9.])
        dark = np.array([0., 0.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(
                        flat_correction(proj, flat[np.newaxis,:], dark[np.newaxis,:], params),
                        np.array([1.0, 0.5, 1.0, 0.5]))
        params.normalization_cutoff = 0.8
        np.testing.assert_array_almost_equal(
                        flat_correction(proj, flat[np.newaxis,:], dark[np.newaxis,:], params),
                        np.array([0.8, 0.5, 0.8, 0.5]))
        params.normalization_cutoff = 1.1 
        flat = np.array([5., 5., 5.5, 5.])
        params.bright_exp_ratio = 0.5
        np.testing.assert_array_almost_equal(
                        flat_correction(proj, flat[np.newaxis,:], dark[np.newaxis,:], params),
                        np.array([1.0, 0.5, 1.0, 0.5]))
        params.flat_correction_method = 'dummy'
        self.assertRaises(ValueError, flat_correction, proj, flat, dark, params)
        

class StripeRemovalTests(TestCase):
    def phantom_prj(self, size=64):
        obj = tomopy.misc.phantom.shepp2d(size=size)
        prj = tomopy.sim.project.project(obj, np.linspace(0, np.pi/2, size))
        prj[:,:,size//2] = 0
        return prj
    
    def test_vo_all(self):
        # Prepare some test data
        prj = self.phantom_prj()
        # Prepare parameters
        params = make_params()
        params.remove_stripe_method = 'vo-all'
        params.vo_all_snr = 5
        params.vo_all_la_size = 5
        params.vo_all_sm_size = 3
        result = remove_stripe(np.copy(prj), params)
        # Compare results
        expected = tomopy.remove_all_stripe(np.copy(prj), snr=5, la_size=5, sm_size=3)
        expected[np.isnan(expected)] = 0
        result[np.isnan(result)] = 0
        np.testing.assert_array_equal(result, expected)
    
    def test_sf(self):
        # Prepare some test data
        prj = self.phantom_prj()
        # Prepare parameters (different from tomopy_cli or tomopy defaults)
        params = make_params()
        params.remove_stripe_method = 'sf'
        params.sf_size = 7
        result = remove_stripe(np.copy(prj), params)
        # Compare results
        expected = tomopy.remove_stripe_sf(np.copy(prj), size=7)
        np.testing.assert_array_equal(result, expected)
    
    def test_fw(self):
        # Prepare some test data
        prj = self.phantom_prj()
        # Prepare parameters (different from tomopy_cli or tomopy defaults)
        params = make_params()
        params.remove_stripe_method = 'fw'
        params.fw_level = 5
        params.fw_filter = "haar"
        params.fw_sigma = 1.3
        result = remove_stripe(np.copy(prj), params)
        # Compare results
        expected = tomopy.remove_stripe_fw(np.copy(prj), level=5, wname="haar", sigma=1.3)
        np.testing.assert_array_equal(result, expected)
    
    def test_ti(self):
        # Prepare some test data
        prj = self.phantom_prj()
        # Prepare parameters (different from tomopy_cli or tomopy defaults)
        params = make_params()
        params.remove_stripe_method = 'ti'
        params.ti_alpha = 1.2
        params.ti_nblock = 2
        result = remove_stripe(np.copy(prj), params)
        # Compare results
        expected = tomopy.remove_stripe_ti(np.copy(prj), alpha=1.2, nblock=2)
        np.testing.assert_array_equal(result, expected)
    
    def test_vo_all(self):
        # Prepare some test data
        prj = self.phantom_prj()
        # Prepare parameters
        params = make_params()
        params.remove_stripe_method = 'vo-all'
        params.vo_all_snr = 5
        params.vo_all_la_size = 5
        params.vo_all_sm_size = 3
        result = remove_stripe(np.copy(prj), params)
        # Compare results
        expected = tomopy.remove_all_stripe(np.copy(prj), snr=5, la_size=5, sm_size=3)
        expected[np.isnan(expected)] = 0
        result[np.isnan(result)] = 0
        np.testing.assert_array_equal(result, expected)


class DataCorrectionTests(TestCase):
    def test_sinogram_max_value(self):
        params = make_params()
        # No effect
        data = np.array([0, 1., 2., 3.])
        params.sinogram_max_value = np.inf
        np.testing.assert_array_equal(cap_sinogram_values(data, params),
                                      [0, 1., 2., 3.])
        # Remove some values
        data = np.array([0, 1.1, 2., np.inf])
        params.sinogram_max_value = 1.
        np.testing.assert_array_equal(cap_sinogram_values(data, params),
                                      [0, 1., 1., 1.])
        # Check float/int values
        data = np.array([0, 1., 2., 3.])
        params.sinogram_max_value = int(2)
        np.testing.assert_array_equal(cap_sinogram_values(data, params),
                                      [0, 1., 2., 2.])
        data = np.array([0, 1., 2., 3.], dtype=int)
        params.sinogram_max_value = 2.
        np.testing.assert_array_equal(cap_sinogram_values(data, params),
                                      [0, 1., 2., 2.])
