from setuptools import setup

setup(
    name="noise_monitor",
    version="0.1",
    description="A python package to control ground stations and perform measurements",
    author="Felix Steinkohl",
    author_email="steinkohl@campus.tu-berlin.de",
    packages=["noise_monitor"],
    scripts=[
        "noise_monitor/noise_monitor.py",
        "noise_monitor/noise_sweeper.py",
        "noise_monitor/rotator_cam.py",
    ],
    install_requires=[
        "numpy",
        "pandas",
        "simplesoapy",
        "simplespectral",
        "soapy_power",
        "pyfftw",
        "azely",
        "opencv-python",
        "plotly",
    ],
)
