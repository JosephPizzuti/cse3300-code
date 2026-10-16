
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

def client_query_server(string, socket):
    """
    takes user input string and sends command to server given a  socket
    returns server response
    """
    socket.send(f"QUERY {string}")
    while True:
        data = socket.recv(1024)
        if not data:
            break

    return data

def handle_server_response(response):
    """
    Takes in a server response and parses the data.
    returns number of matching words and list of matching words
    """
    response_code = response[0]
    if (response_code != 200):
        print(f"Error: Code {response_code}. Please try again")
    num_words = response[1]
    list_words = response[2]

    print(f"Number of words: {num_words}")
    print(f"Word List: {list_words}")

if __name__ == '__main__':
    # TCP Client template, borrowed from hw3 echo-client.py
    serverName = 'localhost'
    serverPort = 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    # send client user input, wait for response, then parse server response
    # still using echo-client.py as reference
    user_input = collect_user_input()
    response = client_query_server(user_input, clientSocket)
    
    # take in server data and print response out
    handle_server_response(response)

    
