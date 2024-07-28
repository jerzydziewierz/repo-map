import pytest
from repo_map_generator import RepoMap, Tag
import os

def test_repo_map_initialization():
    repo_map = RepoMap()
    assert repo_map.root is not None
    assert repo_map.max_map_tokens == 1024
    assert repo_map.verbose is False
    assert repo_map.debug is False

def test_get_rel_fname():
    test_root = os.path.join(os.getcwd(), "test_root")
    repo_map = RepoMap(root=test_root)
    assert repo_map.get_rel_fname(os.path.join(test_root, "file.py")) == "file.py"
    assert repo_map.get_rel_fname(os.path.join(test_root, "dir", "file.py")) == os.path.join("dir", "file.py")

def test_reset_stats():
    repo_map = RepoMap()
    repo_map.stats = {'file_count': 10, 'loc_count': 100, 'total_tokens': 1000, 'tag_count': 50}
    repo_map.reset_stats()
    assert repo_map.stats == {'file_count': 0, 'loc_count': 0, 'total_tokens': 0, 'tag_count': 0}

def test_tag_namedtuple():
    test_root = os.path.join(os.getcwd(), "test_root")
    tag = Tag(rel_fname="file.py", fname=os.path.join(test_root, "file.py"), line=10, name="test_function", kind="def")
    assert tag.rel_fname == "file.py"
    assert tag.fname == os.path.join(test_root, "file.py")
    assert tag.line == 10
    assert tag.name == "test_function"
    assert tag.kind == "def"

# Add more tests as needed for other functions and methods
