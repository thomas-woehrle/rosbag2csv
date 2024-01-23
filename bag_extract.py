import csv
import numpy as np
import os
import rosbag
import sys
import cv2
import datetime

IMG_MSG_TYPES = ['sensor_msgs/Image', 'sensor_msgs/CompressedImage']

def find_first_of_substrings(string, substrings):
    for substring in substrings:
        index = string.find(substring)
        if index != -1:
            return index
    return -1


def filename_from_msg(msg):
    stamp = msg.header.stamp
    timestamp = stamp.to_sec() # get timestamp as float
    nanoseconds = stamp.to_nsec()
    print(timestamp)
    dt_object = datetime.datetime.fromtimestamp(timestamp) # turn into datetime object
    formatted_stamp = dt_object.strftime("%Y%m%d-%H%M%S") # format to year,month,day,hour,minute,second
    return f"{formatted_stamp}-{nanoseconds:09d}" # add padded nanoseconds at the end TODO cut of first digits


def get_img_topics(bag, topics):
    img_topics = set()
    covered_topics = set()
    all_topics = set(topics)

    for topic, msg, t in bag.read_messages(topics=topics):
        if msg._type in IMG_MSG_TYPES:
            img_topics.add(topic)
        covered_topics.add(topic)

        if covered_topics == all_topics:
            break

    return list(img_topics)


def directoryname_from_topic(topic):
    dn = topic.replace('/', '--')

    # try to find the a suitable directory name:
    idx = find_first_of_substrings(dn, ['left', 'right', 'center', 'depth'])
    if idx != -1:
        dn = dn[idx:]

    return dn


def create_img_directories(topics):
    for topic in topics:
        path = directoryname_from_topic(topic)

        try:
            os.makedirs(path, exist_ok=True)
            print(f"Directory '{path}' created")
        except OSError as error:
            print(f"Error: {error}")


def ros_img_to_dict(msg, topic):
    # TODO different handling for depth topics...
    msg_dict = {} # empty dict

    fn = filename_from_msg(msg)
    dn = directoryname_from_topic(topic)

    np_arr = np.frombuffer(msg.data, np.uint8)
    cvimg = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    out_fn = os.path.join(dn, fn + '.png')
    print(out_fn)
    cv2.imwrite(out_fn, cvimg) # overwrites image, if already existing
    msg_dict[dn] = fn

    return msg_dict


def ros_msg_to_dict(msg, parent_key=''):
    """
    Convert a ROS message to a dictionary with nested fields flattened.
    The parent_key parameter is the base of the key for (nested) fields.
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
            """
        # IMPORTANT: handling some lists does not work right now
        # reason for this is: number_of_list_elements is variable, but number of csv columns isn't
        elif isinstance(field_value, list):  # It's a list, could be primitives or messages
            for i, item in enumerate(field_value):
                item_key = f"{new_key}[{i}]"
                if hasattr(item, "__slots__"):  # Nested message in list
                    nested_dict = ros_msg_to_dict(item, parent_key=item_key)
                    msg_dict.update(nested_dict)
                else:  # Primitive type in list
                    msg_dict[item_key] = item"""
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
                # next line means that there will be an image which ist not referenced in the .csv file, but that is okay
                msg_dict = ros_img_to_dict(msg, topic) 
            else:
                msg_dict = ros_msg_to_dict(msg, parent_key=topic)
            field_names.update(msg_dict.keys()) # we only need the keys
            covered_topics.add(topic)

        if covered_topics == all_topics:  
            break

    return sorted(field_names)


if __name__ == '__main__':
    real_bag = 'ts_2022_08_04_15h23m08s_one_row.bag'
    test_bag = 'test.bag'
    time_to_analyze = 2

    input_file = real_bag
    output_file = 'output.csv'
    interval = 0.5

    bag = rosbag.Bag(input_file)
    all_topics = list(bag.get_type_and_topic_info()[1].keys())
    topics = ['/terrasentia/imu', '/terrasentia/zed2/zed_node/left/image_rect_color/compressed']
    bag_start_time = bag.get_start_time()

    img_topics = get_img_topics(bag, topics)
    if img_topics:
        create_img_directories(img_topics)

    most_recent_messages = {} # empty dict, values of this dict will eventually also be dicts
    output_data = [] # empty array

    next_interval_time = bag_start_time + interval 

    counter = 0
    for topic, msg, t in bag.read_messages(topics=topics):
        print(counter)
        counter += 1
        t = t.to_sec()
        if t >= bag_start_time + time_to_analyze:
            break

        if t <= next_interval_time:
            most_recent_messages[topic] = msg
        else:
            # turn the messages into dictionaries
            for topic, msg in most_recent_messages.items():
                if msg._type in IMG_MSG_TYPES:
                    most_recent_messages[topic] = ros_img_to_dict(msg, topic)
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