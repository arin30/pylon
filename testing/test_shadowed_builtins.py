import pytest

from click.testing import CliRunner
from rules.base import Finding
from rules.shadowed_builtins import find_shadowed_builtins
from cli import check
from test_util import create_test_file


def test_cli_reports_shadowed_builtin(tmp_path):
    file = create_test_file(tmp_path, 'list = []\n')

    result = CliRunner().invoke(check, [str(file)])

    assert result.exit_code == 1
    assert ':1: [shadowed-builtin]' in result.output


@pytest.mark.parametrize('code, name', [
    ('list = []', 'list'),
    ('dict: object = {}', 'dict'),
    ('id += 1', 'id'),
    ('(type, other) = values', 'type'),
    ('first, *list = values', 'list'),
    ('if (len := 1): pass', 'len'),
    ('def f(list): pass', 'list'),
    ('async def f(dict): pass', 'dict'),
    ('def f(id, /): pass', 'id'),
    ('def f(*, type): pass', 'type'),
    ('def f(*list, **dict): pass', 'list'),
    ('f = lambda id: id', 'id'),
])
def test_shadowed_builtin_binding(tmp_path, code, name):
    file = create_test_file(tmp_path, code)

    findings = find_shadowed_builtins(str(file))

    assert Finding('shadowed-builtin', f"'{name}' shadows a Python builtin", 1) in findings


@pytest.mark.parametrize('code', [
    'values = list(range(3))',
    'obj.list = values',
    'values["dict"] = 1',
    'def f(list_): return list(list_)',
    '__name__ = "example"',
])
def test_builtin_references_and_other_names_are_not_flagged(tmp_path, code):
    file = create_test_file(tmp_path, code)

    assert find_shadowed_builtins(str(file)) == []


def test_all_bindings_are_reported_in_source_order(tmp_path):
    file = create_test_file(tmp_path, 'def f(*list, **dict):\n    id = 1\n    type = 2\n')

    assert find_shadowed_builtins(str(file)) == [
        Finding('shadowed-builtin', "'list' shadows a Python builtin", 1),
        Finding('shadowed-builtin', "'dict' shadows a Python builtin", 1),
        Finding('shadowed-builtin', "'id' shadows a Python builtin", 2),
        Finding('shadowed-builtin', "'type' shadows a Python builtin", 3),
    ]
