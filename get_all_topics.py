import rosbag 
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='python3 get_all_topics.py', description='Returns all topics present in a rosbag file')
    parser.add_argument('input_filepath', help='The filepath to the input rosbag file')

    args = parser.parse_args()

    bag = rosbag.Bag(args.input_filepath)
    all_topics = bag.get_type_and_topic_info()[1].keys()
    for topic in all_topics:
        print(topic)