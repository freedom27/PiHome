def print_message(message):
    print("Message on topic {} received with payload {}".format(message.topic, message.payload))

def get_actions():
    actions = {}
    actions["print_message"] = print_message
    return actions
