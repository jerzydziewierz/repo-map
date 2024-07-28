from setuptools import setup, find_packages

setup(
    name='repo-map',
    version='0.0.3',
    py_modules=['repo_map_generator'],
    python_requires='>=3.10',
    install_requires=[
        'networkx',
        'numpy',  # Added numpy as a dependency
        'diskcache',
        'grep_ast',
        'pygments',
        'tqdm',
        'tiktoken',
        'tree_sitter_languages==1.10.2',
        'pathspec',
    ],
    entry_points={
        'console_scripts': [
            'repo-map=repo_map_generator:main',
        ],
    },
)
