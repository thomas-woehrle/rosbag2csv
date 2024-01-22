import rosbag
import csv

def ros_msg_to_dict(msg, parent_key=''):
    """
    Convert a ROS message to a dictionary with nested fields flattened.
    :param msg: The ROS message object.
    :param parent_key: The base key for nested fields (used for recursion).
    :return: A dictionary representation of the message.
    THE CORE OF THIS FUNCTION WAS BUILT BY ChatGPT
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
        elif isinstance(field_value, list):  # It's a list, could be primitives or messages
            for i, item in enumerate(field_value):
                item_key = f"{new_key}[{i}]"
                if hasattr(item, "__slots__"):  # Nested message in list
                    nested_dict = ros_msg_to_dict(item, parent_key=item_key)
                    msg_dict.update(nested_dict)
                else:  # Primitive type in list
                    msg_dict[item_key] = item
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
            field_names.update(msg_dict.keys())
            covered_topics.add(topic)

        if covered_topics == topics_set:  # Compare with the pre-made set
            break

    return sorted(field_names)


if __name__ == '__main__':
    bag = rosbag.Bag('test.bag')
    topics = list(bag.get_type_and_topic_info()[1].keys())

    interval = 0.5 # should be inputted as argument to script
    next_interval_time = bag.get_start_time() + interval 

    most_recent_messages = {} # empty dict, values of this dict will also be dicts
    output_data = {} # empty dict

    for topic, msg, t in bag.read_messages(topics=topics):
        if t.to_sec() <= next_interval_time:
            most_recent_messages[topic] = ros_msg_to_dict(msg, parent_key=topic)
        else:
            # combine the dictionaries into a single dictionary 
            combined_dict = {k: v for d in most_recent_messages.values() for k, v in d.items()} 
            output_data[str(t.to_sec())] = combined_dict
            next_interval_time += interval

#    output_file = 'output.csv'
#    with open(output_file, 'w') as file:
#        field_names = collect_all_field_names(bag, topics)

    bag.close()
