"""
Sanic OpenAPI extension.
"""
import pathlib
import re

from setuptools import find_packages, setup

module_init_path = pathlib.Path.cwd() / "sanic_openapi3e" / "__init__.py"
assert module_init_path.exists()
with open(str(module_init_path)) as fp:
    try:
        version = re.findall(r"""^__version__ = ['"]([^'"]+)['"]\r?$""", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version from {}".format(module_init_path))

module_readme = pathlib.Path.cwd() / "README.md"
with open(str(module_readme)) as fp:
    long_description = fp.read()
    long_description_content_type = "text/markdown"
desc = "OpenAPI v3 support for Sanic. Document and describe all parameters, including sanic path params. Python 3.6+"
setup(
    name="sanic-openapi3e",
    version=version,
    url="https://github.com/endafarrell/sanic-openapi3e",
    license="MIT",
    author="Enda Farrell",
    author_email="enda.farrell@gmail.com",
    description=desc,
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    packages=find_packages(exclude=["*tests*", "*examples*"]),
    package_data={"sanic_openapi3e": ["ui/*"]},
    platforms="any",
    install_requires=["sanic>=19.6.0", "pyyaml >= 5.3.1"],
    extras_require={"testing": ["pytest", "pytest-cov"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
