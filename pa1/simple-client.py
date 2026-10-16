
from socket import *

def collect_user_input():
    """
    collects user input in string format until it contains at least one '?'
    returns user input as string
    """
    user_input = input("Enter a string with at least 1 '?': ")
    while user_input.count("?") < 1:
        print("Invalid input. Please try again.")
        user_input = input("Enter a string with at least 1 '?': ")
    return user_input

def handle_server_response(response):
    """
    Takes in a server response and parses the data.
    returns number of matching words and list of matching words
    """
    ...

def display_info(info):
    """
    prints out information from server
    returns nothing
    """
    ...

if __name__ == '__main__':
    # TCP Client template, borrowed from hw3 echo-client.py
    serverName = 'localhost'
    serverPort = 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    # send client user input, wait for response, then parse server response
    # still using echo-client.py as reference
    user_input = collect_user_input()
    clientSocket.send(user_input.encode())
    response = clientSocket.recv(1024)
    refined_info = handle_server_response(response)

    # print out information displayed by server
    display_info(refined_info)
