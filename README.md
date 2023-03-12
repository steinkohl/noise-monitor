The noise monitor package provides tools for:
- The control of remote ground station
- The localisation of noise sources
- The tracking of astronomical objects
- The streaming of augmented webcam footage of the GS
- The presentation of PSD noise measurements


### Install Guide ###

0. Clone this Repository
1. Install SoapySDR and the needed drivers for your SDR
2. Install OpenCV with `sudo apt-get install python3-opencv -y`
3. Install Python Package with `python setup.py install`


### Usage ###
Once installed, the package provides three scripts, which can be executed in the terminal:
    
> noise_sweeper.py -h

The noise sweeper is a tool to collect noise measurement data from ground stations, 
and provide a graphical representation of the results.
The help command as shown should provide all necessary information. 
An example of a ground station config file is shown in the config directory.

> noise_monitor.py -h

The noise monitor is a part of the noise sweeper but only capable of presenting previously recorded data.
The help command as shown should provide all necessary information. 
An example of a ground station config file is shown in the config directory.

> rotator_cam.py -h

The rotator cam enable the streaming of the webcam video to a remote location.
The video also will be augmented by an overlay containing important GS data.
An example of a ground station config file is shown in the config directory.