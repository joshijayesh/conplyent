from setuptools import setup


setup(
    name="conplyent",
    version="0.0.0",
    license="MIT",
    author="Jayesh Joshi",
    author_email="jayeshjo1@utexas.edu",
    url="https://github.com/joshijayesh/conplyent/",
    description="Local and Remote Console executor",
    packages=["conplyent"],
    install_requires=["pyzmq>=17.1.2"],
)
