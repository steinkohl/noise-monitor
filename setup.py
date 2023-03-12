from setuptools import setup, find_packages

setup(
    name="noise_monitor",
    version="0.3.2",
    description="A python package to control ground stations and perform measurements",
    author="Felix Steinkohl",
    author_email="steinkohl@campus.tu-berlin.de",
    packages=find_packages(),
    scripts=[
        "noisemonitor/noise_monitor.py",
        "noisemonitor/noise_sweeper.py",
        "noisemonitor/rotator_cam.py",
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
        "dash",
        "lmfit",
    ],
)
