from fsl.utils.filetree import utils
import pytest


def test_variables():
    assert ('var', 'other_var', 'var') == tuple(utils.find_variables('some{var}_{other_var}_{var}'))
    assert ('var', 'other_var', 'var') == tuple(utils.find_variables('some{var}_[{other_var}_{var}]'))
    assert {'other_var'} == utils.optional_variables('some{var}_[{other_var}_{var}]')


def test_get_variables():
    assert {'var': 'test'} == utils.extract_variables('{var}', 'test')
    assert {'var': 'test'} == utils.extract_variables('2{var}', '2test')
    assert {'var': 'test', 'other_var': None} == utils.extract_variables('{var}[_{other_var}]', 'test')
    assert {'var': 'test', 'other_var': 'foo'} == utils.extract_variables('{var}[_{other_var}]', 'test_foo')
    assert {'var': 'test', 'other_var': 'foo'} == utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo_test')
    assert {'var': 'test', 'other_var': None} == utils.extract_variables('{var}[_{other_var}]_{var}', 'test_test')
    with pytest.raises(ValueError):
        utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo')
    with pytest.raises(ValueError):
        utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo_bar')
    with pytest.raises(ValueError):
        utils.extract_variables('bar{var}[_{other_var}]_{var}', 'test')

    assert {'subject': '01', 'session': 'A'} == utils.extract_variables('sub-{subject}/[ses-{session}]/T1w.nii.gz', 'sub-01/ses-A/T1w.nii.gz')
    with pytest.raises(ValueError):
        utils.extract_variables('sub-{subject}/[ses-{session}]/T1w.nii.gz', 'sub-01/other/T1w.nii.gz')


def test_multiple_optionals():
    with pytest.raises(KeyError):
        utils.extract_variables('{var}[_{opt1}][_{opt2}]', 'test_foo')
    assert {'var': 'test', 'opt1': None, 'opt2': None} == utils.extract_variables('{var}[_{opt1}][_{opt2}]', 'test')
    assert {'var': 'test', 'opt1': 'oo', 'opt2': None} == utils.extract_variables('{var}[_f{opt1}][_{opt2}]', 'test_foo')


