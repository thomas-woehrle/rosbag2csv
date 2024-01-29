import csv
import numpy as np
import os
import rosbag
import sys
import cv2
import json
from cv_bridge import CvBridge
from utils import create_img_directories, directoryname_from_topic, filename_from_msg, get_img_topics
from arg_parsing import parser

IMG_MSG_TYPES = ['sensor_msgs/Image', 'sensor_msgs/CompressedImage']
CV_BRIDGE = CvBridge()

def ros_img_to_dict(msg, topic, output_directory):
    """
    Save file of picture of inputted ROS msg and return a dictionary with one key-value pair.
    The key is the folder_name, the value is the filename of the picture of the inputted msg.
    """
    msg_dict = {} # empty dict

    fn = filename_from_msg(msg)
    dn = directoryname_from_topic(topic)
    out_path = os.path.join(output_directory, dn, fn + '.png')

    if msg._type == 'sensor_msgs/Image':
        cvimg = CV_BRIDGE.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        cv2.imwrite(out_path, cvimg)

    elif msg._type == 'sensor_msgs/CompressedImage':
        np_arr = np.frombuffer(msg.data, np.uint8)
        cvimg = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        cv2.imwrite(out_path, cvimg) # overwrites image, if already existing. Does nothing if directory non-existant

    msg_dict[dn] = fn
    return msg_dict


def ros_msg_to_dict(msg, parent_key=''):
    """
    Convert a ROS message to a dictionary with nested fields flattened.
    The parent_key parameter is the base of the key for (nested) fields.
    NOTE certain ROS messages that have list fields make problems
    """
    msg_dict = {}
        
    # Iterate over all fields in the message
    for field_name in msg.__slots__:
        field_value = getattr(msg, field_name)

        # Construct the new key by concatenating the parent key and field name
        new_key = f'{parent_key}.{field_name}' if parent_key else field_name

        if hasattr(field_value, "__slots__"):  # It's a nested message
            # Recursively process the nested message
            nested_dict = ros_msg_to_dict(field_value, parent_key=new_key)
            msg_dict.update(nested_dict)
        else:  # Primitive type
            msg_dict[new_key] = field_value

    return msg_dict


def collect_all_field_names(bag, topics):
    """
    Collect all field names from at least one message per topic. 
    Returns an alphabetically sorted list of the field names. 
    """
    field_names = set()
    covered_topics = set()
    all_topics = set(topics)

    for topic, msg, t in bag.read_messages(topics=topics):
        if topic not in covered_topics:   
            if msg._type in IMG_MSG_TYPES:
                # specifying a non-existant directory means that no image will be saved in ros_img_to_dict()
                msg_dict = ros_img_to_dict(msg, topic, './can_be_deleted', ) 
            else:
                msg_dict = ros_msg_to_dict(msg, parent_key=topic)
            field_names.update(msg_dict.keys()) # we only need the keys
            covered_topics.add(topic)

        if covered_topics == all_topics:  
            break

    return sorted(field_names)


def get_topics_from_arg(bag, arg_topics):
    excluded_topics = ['/rosout', '/tf', '/tf_static']
    topics = set()
    for arg in arg_topics:
        if arg == 'all':
            new_topics = bag.get_type_and_topic_info()[1].keys()
            type(new_topics)
            topics.update(set(new_topics)) # all topics
            break
        elif arg.endswith('.json'):
            try:
                with open(arg, 'r') as file:
                    new_topics = json.load(file)
                    topics.update(set(new_topics))
            except Exception:
                print('Error while reading', arg)
                print('Make sure to supply correct path.')
                sys.exit(1)
        else:
            topics.add(arg)
    
    topics = list(topics)
    topics = [topic for topic in topics if not topic in excluded_topics]
    return sorted(topics)
    

def main(input_file, interval, arg_topics, output_directory, output_file, extraction_delay, length_of_extraction):
    bag = rosbag.Bag(input_file)
    topics = get_topics_from_arg(bag, arg_topics)
    extraction_start = bag.get_start_time() + extraction_delay 
    extraction_end = extraction_start + length_of_extraction if length_of_extraction else bag.get_end_time() 

    img_topics = get_img_topics(bag, topics, IMG_MSG_TYPES)
    if img_topics:
        create_img_directories(output_directory, img_topics)

    most_recent_messages = {} # empty dict, values of this dict will eventually also be dicts
    output_data = [] # empty array

    next_interval_time = extraction_start + interval 

    for topic, msg, t in bag.read_messages(topics=topics):
        t = t.to_sec()
        if t >= extraction_end:
            break

        if t <= next_interval_time:
            most_recent_messages[topic] = msg
        else:
            # turn the messages into dictionaries
            for topic, msg in most_recent_messages.items():
                if msg._type in IMG_MSG_TYPES:
                    most_recent_messages[topic] = ros_img_to_dict(msg, topic, output_directory)
                else:
                    most_recent_messages[topic] = ros_msg_to_dict(msg, parent_key=topic)
            # combine the dictionaries into a single dictionary 
            combined_dict = {k: v for d in most_recent_messages.values() for k, v in d.items()} 
            output_data.append(combined_dict)
            next_interval_time += interval

    try:
        with open(output_file, 'w') as file:
            fieldnames = collect_all_field_names(bag, topics)

            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for item in output_data:
                try:
                    writer.writerow(item)
                except ValueError as e:
                    print()
                    print(f"ValueError occurred: {e}", file=sys.stderr)
                    print('------')
                    print("Try removing topics where the msgs have lists as fields")
                    sys.exit(1)
    finally: 
        bag.close()

    sys.exit(0)

if __name__ == '__main__':
    args = parser.parse_args()

    input_file = args.input_filepath
    interval = args.interval
    arg_topics = args.topics # the actual topics will be determined after the bag is opened
    output_directory = args.output_directory # should have default like './'
    output_file = os.path.join(output_directory, 'rosbag.csv')
    extraction_delay = args.delay
    length_of_extraction = args.length

    main(input_file, interval, arg_topics, output_directory, output_file, extraction_delay, length_of_extraction)