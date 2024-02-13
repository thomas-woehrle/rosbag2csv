import argparse

parser = argparse.ArgumentParser(
    prog='python3 rosbag2csv.py', 
    description='Extracts data from a .bag file into a csv with frequency synchronization and image extraction',
    epilog="NOTE: Don't use topics that use the nav_msgs/Path ROS message type. The first save takes place at <start_time> + <interval_time>. The last (partially finished) interval are excluded. An empty output file could mean that you specified the topics wrongly")

parser.add_argument('input_filepath', help='The path to the input rosbag-file. Can be relative or absolute.')
parser.add_argument('interval', type=float, help='The interval with which extraction out of the rosbag file takes place. Should not be smaller than 1/lowest_frequency.')
parser.add_argument('topics', nargs='+', help='The topics that should be processed on the rosbag file. Can be supplied via multiple command line arguments, a json file (a single list), or a mixture of both. Write "all" to include all topics.')

parser.add_argument('-o', '--out-dir', metavar='', dest='output_directory', default='./', help='The path to the output directory. (Default: the current directory)')
parser.add_argument('-d', '--delay', metavar='', type=float, default=0, help='The number of seconds from the beginning of the rosbag-file that the extraction should be delayed by. (Default: 0)')
parser.add_argument('-l', '--length', metavar='', type=float, help='The length of the extraction period in seconds. (Default: Until end of rosbag-file)')