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
        "dotmap",
        "loguru",
        "pykep",
        "scikit-spatial",
        "toml",
        "tqdm",
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
    ],
    python_requires=">=3.8,<3.9",
    project_urls={
        "Source": "https://github.com/aidotse/paseos/",
    },
)
