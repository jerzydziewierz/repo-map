from setuptools import setup, find_packages

setup(
    name='repo-map',
    version='0.0.1',
    py_modules=['repo_map_generator'],
    install_requires=[
        'networkx',
        'diskcache',
        'grep_ast',
        'pygments',
        'tqdm',
        'tiktoken',
        'tree_sitter_languages',
        'pathspec',
    ],
    entry_points={
        'console_scripts': [
            'repo-map=repo_map_generator:main',
        ],
    },
)
