import rosbag

bag = rosbag.Bag('test.bag')
topics = list(bag.get_type_and_topic_info()[1].keys())

for topic, msg, t in bag.read_messages(topics=topics):
    print(msg)
    
bag.close()