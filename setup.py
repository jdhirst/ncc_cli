import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ncc_cli",
    version="0.0.1",
    author="James Hirst",
    author_email="jdhirst@hirstgroup.net",
    description="A small command-line client for NextCloud/ownCloud",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jdhirst1/ncc_cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: GPL-3",
        "Operating System :: OS Independent",
    ],
)