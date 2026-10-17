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

def client_query_server(query_string, sock):
    """
    takes user input string and sends QUERY command to server over TCP socket
    receives  server response across multiple chunks until EOF
    returns server response as a decoded string.
    """
    #  application protocol request format: "QUERY <string>\n"
    # encode string into bytes for the socket
    # we use sendall() to ensure the entire message is sent to the server
    # ref: https://docs.python.org/3/howto/sockets.html#using-a-socket:~:text=Using%20a%20Socket
    request = f"QUERY {query_string}\n"
    sock.sendall(request.encode('utf-8'))

    # we need to recv chunks in a loop because the size of server reponse can change dramatically
    # i.e. 10's words < -- > 10000s of words
    # we can loop until the server stops responding
    # ref: https://docs.python.org/3/library/socket.html#socket.socket.recv:~:text=recv%28bufsize%5B%2C%20flags%5D%29%C2%B6
    response_chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_chunks.append(chunk.decode('utf-8'))

    # combine all chunks into one string
    return "".join(response_chunks)

def handle_server_response(response):
    """
    takes in a server response string, validates status code,
    and extracts number of matching words and the list of words
    returns nothing and prints results
    """
    if not response:
        print("Error: Empty response received from server.")
        return

    # response split into lines under following application protocol:
    # Line 1: Status (i.e. "200 OK" or "404 NOT FOUND")
    # Line 2: Count of matching words (i.e. "COUNT <n>")
    # Line 3+: matching words
    lines = response.strip().splitlines()
    if not lines:
        print("Error: No data in response.")
        return

    status_line = lines[0]
    status_parts = status_line.split()
    status_code = status_parts[0] if status_parts else ""

    if status_code != "200":
        print(f"Error from server: {status_line}")
        return

    # extract word count from second line formatted as "COUNT <int>"
    # get rest of lines
    num_words = int(lines[1].split()[1])
    matching_words = lines[2:]

    print(f"Status: {status_line}")
    print(f"Number of matching words: {num_words}")
    print("Matching words:")
    for word in matching_words:
        print(word)

if __name__ == '__main__':
    # tcp client setup, borrowed from hw3 echo-client.py
    # ref: https://docs.python.org/3/library/socket.html
    serverName = 'localhost'
    serverPort = 12000

    # create TCP stream socket and connect to server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    # collect input with at least one '?'
    user_input = collect_user_input()

    # send query to server and receive full response
    response = client_query_server(user_input, clientSocket)

    # close connection after query is complete
    clientSocket.close()

    # parse and display results
    handle_server_response(response)


    
