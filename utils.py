import datetime
import os


def create_img_directories(output_directory, topics):
    for topic in topics:
        path = os.path.join(output_directory, directoryname_from_topic(topic))

        try:
            os.makedirs(path, exist_ok=True)
        except OSError as error:
            print(f"Error: {error}")


def directoryname_from_topic(topic):
    dn = topic.replace('/', '--')

    # try to find the a suitable directory name:
    idx = find_first_of_substrings(dn, ['left', 'right', 'center', 'depth'])
    if idx != -1:
        dn = dn[idx:]

    return dn


def find_first_of_substrings(string, substrings):
    for substring in substrings:
        index = string.find(substring)
        if index != -1:
            return index
    return -1


def filename_from_msg(msg):
    # TODO if milliseconds of timestampt not available, then this collapses all images
    # within a second into one
    t = msg.header.stamp.to_sec()
    dt_object = datetime.datetime.fromtimestamp(t)  # turn into datetime object
    # format to year,month,day,hour,minute,second
    formatted_stamp = dt_object.strftime("%Y%m%d-%H%M%S")
    # add non-decimal part of seconds at the end
    return f"{formatted_stamp}-{str(t)[11:15]}"


def get_img_topics(bag, topics, img_topics_list):
    img_topics = set()
    covered_topics = set()
    all_topics = set(topics)

    for topic, msg, t in bag.read_messages(topics=topics):
        if msg._type in img_topics_list:
            img_topics.add(topic)
        covered_topics.add(topic)

        if covered_topics == all_topics:
            break

    return list(img_topics)
