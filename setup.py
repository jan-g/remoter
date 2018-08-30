import os.path
from setuptools import setup, find_packages


def read_file(fn):
    with open(os.path.join(os.path.dirname(__file__), fn)) as f:
        return f.read()

setup(
    name="remoter",
    version="0.0.1",
    description="remoter framework",
    long_description=read_file("README.md"),
    author="jang",
    author_email="",
    license=read_file("LICENCE.md"),

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'server = example.cmd:server',
            'client = example.cmd:client',
            'batsrv = battleships.cmd:server',
            'batcli = battleships.cmd:client',
        ],
    },

    install_requires=[
                      "argcomplete",
                      "flask",
                      "requests",
                     ],
    tests_require=[
                    "pytest",
                    "flake8",
                  ],
)
