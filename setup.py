from setuptools import setup, find_packages
from pathlib import Path

# Lire version
version_file = Path(__file__).parent / "src" / "hyperion" / "__version__.py"
version = {}
exec(version_file.read_text(), version)

# Lire README
readme = (Path(__file__).parent / "README.md").read_text()

# Lire requirements
requirements = (Path(__file__).parent / "requirements.txt").read_text().splitlines()
requirements = [r.strip() for r in requirements if r.strip() and not r.startswith("#")]

setup(
    name="hyperion",
    version=version["__version__"],
    author="Matthieu Ryckembusch",
    author_email="matthieu@irun.fr",
    description="Git Repository Profiler & Knowledge Graph Platform",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kortazo/hyperion",
    
    # IMPORTANT: package_dir pour src/ layout
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    # Inclure templates et données
    package_data={
        "hyperion": ["../templates/**/*"],
    },
    include_package_data=True,
    
    install_requires=requirements,
    python_requires=">=3.10",
    
    entry_points={
        "console_scripts": [
            "hyperion=hyperion.cli.main:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
)
