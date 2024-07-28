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
pip install -e .
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.

## License

This project is [licensed](LICENSE).

## Acknowledgments

- inspired by https://github.com/paul-gauthier/aider

