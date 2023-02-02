# Always prefer setuptools over distutils
from setuptools import setup

setup(
    name="paseos",
    version="0.1.0",
    description="A package which simulates the space environment for operating multiple spacecraft.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aidotse/paseos",
    author="Φ-lab@Sweden",
    author_email="pablo.gomez@esa.int",
    include_package_data=True,
    install_requires=[
        "dotmap>=1.3.30",
        "loguru>=0.6.0",
        "matplotlib-base>=3.6.0",
        "pykep>=2.6",
        "scikit-spatial>=6.5.0",
        "skyfield>=1.45",
        "toml>=0.10.2",
        "tqdm>=4.64.1",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.8",
    ],
    packages=[
        "paseos",
        "paseos.activities",
        "paseos.actors",
        "paseos.communication",
        "paseos.power",
        "paseos.utils",
        "paseos.visualization",
    ],
    python_requires=">=3.8,<3.9",
    project_urls={
        "Source": "https://github.com/aidotse/paseos/",
    },
)
