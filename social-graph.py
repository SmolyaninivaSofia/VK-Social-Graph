import json
from os.path import exists as file_exists
from random import randint
from time import sleep
from os import makedirs
import networkx as nx
from vk_api_folder import vk_api
from settings import token, my_id, my_name

def delay():
    """Sleep 0.3-0.4 seconds"""
    try:
        sleep(randint(3, 4) / 10)
    except KeyboardInterrupt:
        exit()


def FilterInformation(user_data):
    return {"id": user_data["id"],
            "name": user_data["first_name"] + "/n" + user_data["last_name"],
            "sex": user_data["sex"]}


def UserInformation(user_id):
    try:
        user_data =  vk.users.get(user_ids=user_id, fields="sex")[0]
    except vk_api.VkApiError:
        return None
    return FilterInformation(user_data)

def UserFriends(user_id ):
    try:
        friends = vk.friends.get(user_id=user_id, order="hints", fields="sex").get("items", None)
    except vk_api.VkApiError:
        return []
    friends_list= []
    for user_data in friends:
        friends_list.append(FilterInformation(user_data))
    return friends_list

if __name__=='__main__':
    #Creatte session
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    cache_dir = "cache/"
    makedirs(cache_dir, exist_ok=True)
    friendship_tree_path = cache_dir+"tree-{}.json".format(my_id)
    networkx_graph_path = cache_dir+"graph-{}.gpickle".format(my_id)

    if file_exists(friendship_tree_path):
        with open(friendship_tree_path, "r") as f:
            friendship_tree = json.load(f)
        print("Friendship tree for user {} loaded from cache".format(my_id))
        print (friendship_tree)
    else:
        friendship_tree = []
        root_user_friends = UserFriends(my_id)
        for n, friend in enumerate(root_user_friends, start=1):
            print("Fetching friends and friends of friends: {}/{}...".format(n, len(root_user_friends)), end="\r")
            friends_of_friend = UserFriends(friend["id"])
            friend.update({"friends": friends_of_friend})
            friendship_tree.append(friend)
            delay()
        print()
        with open(friendship_tree_path, "w") as f:
            json.dump(friendship_tree, f, indent=2)
        print("Friendship tree for user {} saved to {}...".format(my_id, friendship_tree_path))

    if file_exists(networkx_graph_path):
        G = nx.readwrite.read_gpickle(networkx_graph_path)
        print("Graph data for user {} loaded from cache".format(my_id))
    else:
        print("Building base graph...")
        G = nx.Graph()
        G.add_node(my_id, Label=my_name)
        for friend in friendship_tree:
            G.add_node(friend["id"],Label=friend["name"])
            # connect root user to his primary friends
            G.add_edge(my_id, friend["id"])

        for n, primary_friend in enumerate(friendship_tree, start=1):
            print("Processing graph: {}/{}...".format(n, len(friendship_tree)), end="\r")
            for user_x in primary_friend["friends"]:
                if user_x['id'] in G._node.keys():
                    G.add_edge(user_x["id"], primary_friend["id"])

        print()
        filename = my_name+" VK friends.gexf"
        nx.write_gexf(G, filename)
        nx.readwrite.write_gpickle(G, networkx_graph_path)
        print("Graph data saved to {}".format(networkx_graph_path))



