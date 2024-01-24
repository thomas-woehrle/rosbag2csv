# rosbag2csv
This program converts a rosbag file into a csv file, where the individual messages are broken down into scalar values. Images are saved in a separate folder and linked to from the csv file via their name. Users can specify topics to extract, the intervals between extraction, the starting point and timeframe of extraction, etc. 

## Installation
Users must have ROS installed (f.e. Noetic). 
Additionally, Numpy and cv2 must be installed (f.e. via pip).

## Usage
The --help explains everything:
```
usage: python3 rosbag2csv.py [-h] [-o] [-d] [-l] input_filepath interval topics [topics ...]

Extracts data from a .bag file into a csv with frequency synchronization and image extraction

positional arguments:
  input_filepath   The path to the input rosbag-file. Can be relative or absolute.
  interval         The interval with which extraction out of the rosbag file takes place. Should not be smaller than
                   1/lowest_frequency.
  topics           The topics that should be processed on the rosbag file. Can be supplied via multiple command line
                   arguments, a json file (a single list), or a mixture of both. Write "all" to include all topics.

optional arguments:
  -h, --help       show this help message and exit
  -o , --out-dir   The path to the output directory. The directory has to exist already. (Default: the current
                   directory)
  -d , --delay     The number of seconds from the beginning of the rosbag-file that the extraction should be delayed by.
                   (Default: 0)
  -l , --length    The length of the extraction period in seconds. (Default: Until end of rosbag-file)

TIPS: Don't use topics that use the nav_msgs/Path ROS message type. The first second and the last (partially finished) interval are excluded. An empty output file could mean that you
specified the topics wrongly
```

## Acknowledgements
This tool was originally desgined for use on the terrasentia dataset of Jose Cuaran (github.com/jrcuaranv/terrasentia-dataset). 
The extraction of images was adapted from his repository. 

Written by Thomas Woehrle (github.com/thomas-woehrle) in January 2024 at the University of Illinois Urbana-Champaign.
Supervised by Arun V Sivakumar.





