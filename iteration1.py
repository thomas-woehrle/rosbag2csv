import rosbag

def write_messages_to_csv(dict_of_topics_and_msgs):
    pass

bag = rosbag.Bag('test.bag')
topics = list(bag.get_type_and_topic_info()[1].keys())

interval = 0.5 # should be inputted as argument to script
next_interval_time = bag.get_start_time() + interval 

most_recent_messages={} # empty dict

for topic, msg, t in bag.read_messages(topics=topics):
    if t.to_sec() <= next_interval_time:
        most_recent_messages[topic] = msg
    else:
        write_messages_to_csv(most_recent_messages)
        next_interval_time += interval
    
bag.close()