# Repo Map Generator

Repo Map Generator is a tool that creates a structured representation of your repository, highlighting key files, functions, and their relationships. It's designed to help developers quickly understand the structure and complexity of a codebase.

## Features

- Generates a tree-like structure of your repository
- Identifies and ranks important code elements
- Provides statistics about the codebase (file count, lines of code, etc.)
- Supports multiple programming languages
- Ignores files based on .gitignore and .aiderignore

## Installation

To install Repo Map Generator, run:

```
pip install repo-map
```

## Usage

To generate a map of your repository, navigate to your project's root directory and run:

```
repo-map
```

You can also specify a different directory:

```
repo-map /path/to/your/repo
```

## Output

Repo Map Generator will output:
1. A tree-like structure of your repository
2. Statistics about your codebase

## GitHub Action

This repository includes a GitHub Action that runs Repo Map Generator on every push to the main branch and every pull request. The output is saved as an artifact that you can download and review.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
