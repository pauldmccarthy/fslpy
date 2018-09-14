from fsl.utils.filetree import utils
import pytest


def test_variables():
    assert ('var', 'other_var', 'var') == tuple(utils.find_variables('some{var}_{other_var}_{var}'))
    assert ('var', 'other_var', 'var') == tuple(utils.find_variables('some{var}_[{other_var}_{var}]'))
    assert {'other_var'} == utils.optional_variables('some{var}_[{other_var}_{var}]')


def test_get_variables():
    assert {'var': 'test'} == utils.extract_variables('{var}', 'test')
    assert {'var': 'test'} == utils.extract_variables('2{var}', '2test')
    assert {'var': 'test'} == utils.extract_variables('{var}[_{other_var}]', 'test')
    assert {'var': 'test', 'other_var': 'foo'} == utils.extract_variables('{var}[_{other_var}]', 'test_foo')
    assert {'var': 'test', 'other_var': 'foo'} == utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo_test')
    assert {'var': 'test'} == utils.extract_variables('{var}[_{other_var}]_{var}', 'test_test')
    with pytest.raises(ValueError):
        utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo')
    with pytest.raises(ValueError):
        utils.extract_variables('{var}[_{other_var}]_{var}', 'test_foo_bar')
    with pytest.raises(ValueError):
        utils.extract_variables('bar{var}[_{other_var}]_{var}', 'test')
