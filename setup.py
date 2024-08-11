from setuptools import setup, find_packages

setup(
    name='repo-map',
    version='0.0.3',
    py_modules=['repo_map_generator'],
    python_requires='>=3.9',
    install_requires=[
        'networkx',
        'numpy',  # numpy is a missing dependency of networkx that prevents this repo from running standalone.
        'scipy',  # scipy is a missing dependency of networkx that prevents this repo from running standalone.
        'diskcache',
        'grep_ast',
        'pygments',
        'tqdm',
        'tiktoken',
        'tree_sitter_languages==1.10.2',
        'pathspec',
    ],
    extras_require={
        'dev': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'repo-map=repo_map_generator:main',
        ],
    },
)
