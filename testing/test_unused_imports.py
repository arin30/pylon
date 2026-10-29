# run from project root
from rules.base import Finding
from rules.unused_imports import find_unused_imports
from test_util import create_test_file

def test_detects_unused_imports(tmp_path):
    code = """
import os
import sys
from collections import Counter

print(os.getcwd())
"""
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == [Finding(rule_id="unused-import", message="Unused import from 'sys'", line=3),
                      Finding(rule_id="unused-import", message="Unused import from 'Counter'", line=4)]

def test_all_imports_used(tmp_path):
    code = """
import os
print(os.getcwd())
"""
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == []
    
def test_no_imports(tmp_path):
    code = "print('hello')"
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == []

def test_aliased_unused_imports(tmp_path):
    code = """
import os
import numpy as lumpy

print(os.getcwd())
"""
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == [Finding(rule_id="unused-import", message="Unused import from 'lumpy'", line=3)]
    
def test_deliberate_re_export_unused_imports(tmp_path):
    code = "from .app import Flask as Flask\n"
    
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == []

def test_re_export_and_positive_unused_imports(tmp_path):
    code = """
import os
import sys
from .app import Flask as Flask

print(os.getcwd())
"""
    file = create_test_file(tmp_path, code)
    
    result = find_unused_imports(str(file))
    
    assert result == [Finding(rule_id="unused-import", message="Unused import from 'sys'", line=3)]
    
def test_all_double_underscore_marks_import_as_used(tmp_path):
    code = """
from .core import array
from .core import ndarray

__all__ = ["array", "ndarray"]
"""
    file = create_test_file(tmp_path, code)

    result = find_unused_imports(str(file))

    assert result == []

def test_all_double_underscore_with_positive_unused_import(tmp_path):
    code = """
from .core import array
from .core import ndarray
import sys

__all__ = ["array", "ndarray"]
"""
    file = create_test_file(tmp_path, code)

    result = find_unused_imports(str(file))

    assert result == [Finding(rule_id="unused-import", message="Unused import from 'sys'", line=4)]

def test_dotted_import_binds_top_level_package(tmp_path):
    file = create_test_file(tmp_path, 'import os.path\nprint(os.path.join("a", "b"))\n')

    assert find_unused_imports(str(file)) == []


def test_deeply_dotted_import_binds_top_level_package(tmp_path):
    file = create_test_file(tmp_path, 'import xml.etree.ElementTree\nprint(xml.etree.ElementTree)\n')

    assert find_unused_imports(str(file)) == []


def test_dotted_import_alias_is_respected(tmp_path):
    file = create_test_file(tmp_path, 'import os.path as path\nprint(path.join("a", "b"))\n')

    assert find_unused_imports(str(file)) == []


def test_unused_dotted_import_keeps_full_name_in_message(tmp_path):
    file = create_test_file(tmp_path, 'import os.path\n')

    assert find_unused_imports(str(file)) == [
        Finding('unused-import', "Unused import from 'os.path'", 1)
    ]


def test_dotted_from_import_still_requires_imported_name(tmp_path):
    file = create_test_file(tmp_path, 'from xml.etree import ElementTree\nprint(xml)\n')

    assert find_unused_imports(str(file)) == [
        Finding('unused-import', "Unused import from 'ElementTree'", 1)
    ]
