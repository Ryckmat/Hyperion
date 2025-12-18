from setuptools import setup, find_packages
from pathlib import Path

# Lire README
readme = Path("README.md").read_text(encoding="utf-8")

# Lire version
version_file = Path("hyperion/__version__.py").read_text()
version = {}
exec(version_file, version)

setup(
    name="hyperion",
    version=version["__version__"],
    description="Git Repository Profiler & Knowledge Graph",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Matthieu Ryckembusch",
    author_email="matthieu@irun.fr",
    url="https://github.com/Ryckmat/Hyperion",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "click>=8.1.0",
        "neo4j>=5.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hyperion=hyperion.cli.main:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Version Control :: Git",
    ],
)
