import csv
import numpy as np
import os
import rosbag
import sys
import cv2
import rospy
import datetime

def filename_from_msg(msg):
    timestamp = msg.header.stamp.to_sec() # get timestamp as float
    print(timestamp)
    dt_object = datetime.datetime.fromtimestamp(timestamp) # turn into datetime object
    return dt_object.strftime("%Y%m%d-%H%M%S") # format


def ros_msg_to_dict(msg, parent_key=''):
    """
    Convert a ROS message to a dictionary with nested fields flattened.
    The parent_key parameter is the base of the key for (nested) fields.
    """
    msg_dict = {}
    
    # should be refactored into separate function
    # if msg._type == 'sensor_msgs/CompressedImage':
    """
        # return 
        # fn = format(((rospy.rostime.Time.to_nsec(t)/1e9) - 0), '.6f')
        # print('timestamp', fn)
        t = msg.header.stamp
        print(t)
        np_arr = np.frombuffer(msg.data, np.uint8)
        cvimg = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        out_fn = os.path.join('/home/tomwoe/Documents/ros_extraction/left_imgs', str(t.to_nsec()) + '.png')
        print(out_fn)
        cv2.imwrite(out_fn, cvimg)
        msg_dict['left_images'] = out_fn
    """
        
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
    Returns a alphbetically sorted list of the field names. 
    """
    field_names = set()
    covered_topics = set()
    topics_set = set(topics)

    for topic, msg, t in bag.read_messages(topics=topics):
        if topic not in covered_topics:
            msg_dict = ros_msg_to_dict(msg, parent_key=topic)
            field_names.update(msg_dict.keys()) # we only need the keys
            covered_topics.add(topic)

        if covered_topics == topics_set:  
            break

    return sorted(field_names)


if __name__ == '__main__':
    real_bag = 'ts_2022_08_04_15h23m08s_one_row.bag'
    test_bag = 'test.bag'
    time_to_analyze = 10

    input_file = real_bag
    output_file = 'output.csv'
    interval = 0.5

    bag = rosbag.Bag(input_file)
    all_topics = list(bag.get_type_and_topic_info()[1].keys())
    topics = ['/terrasentia/full_gps', '/terrasentia/imu']
    bag_start_time = bag.get_start_time()

    most_recent_messages = {} # empty dict, values of this dict will also be dicts
    output_data = [] # empty array

    next_interval_time = bag_start_time + interval 

    for topic, msg, t in bag.read_messages(topics=topics):
        t = t.to_sec()
        if t >= bag_start_time + time_to_analyze:
            break

        if t <= next_interval_time:
            most_recent_messages[topic] = ros_msg_to_dict(msg, parent_key=topic)
        else:
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