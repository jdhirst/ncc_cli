import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ncc_cli",
    version="0.0.7",
    author="James Hirst",
    author_email="jdhirst@hirstgroup.net",
    description="A small command-line client for NextCloud/ownCloud",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jdhirst1/ncc_cli",
    packages=setuptools.find_packages(),
    install_requires=[
        'pyocclient',
        'humanize',
        'tqdm',
        'yaspin',
        'texttable',
        'configparser'
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'ncc = ncc_cli.ncc_cli:main',
        ]
    }
)
