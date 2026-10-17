from socket import *

# identical to simple-client
def collect_user_input():
    """
    collects user input in string format until it contains at least one '?' or is 'quit'
    returns user input as string
    """
    user_input = input("Enter a string with at least 1 '?' (or 'quit' to exit): ").strip()
    while user_input.lower() != "quit" and user_input.count("?") < 1:
        print("Invalid input. Please try again.")
        user_input = input("Enter a string with at least 1 '?' (or 'quit' to exit): ").strip()
    return user_input

def client_query_server(query_string, sock):
    """
    takes user input string and sends QUERY command to server over TCP socket
    receives server response across multiple chunks until all expected lines have arrived
    returns server response as a decoded string
    """
    # format application protocol request: "QUERY <string>\n"
    # ref: https://docs.python.org/3/howto/sockets.html#using-a-socket:~:text=Using%20a%20Socket
    request = f"QUERY {query_string}\n"
    sock.sendall(request.encode('utf-8'))

    # since connection stays open across multiple queries, we cannot wait for EOF
    # we accumulate chunks and parse COUNT <n> from header to know total lines expected
    # ref: https://docs.python.org/3/howto/sockets.html#using-a-socket:~:text=Using%20a%20Socket%C2%B6
    buffer = ""
    expected_lines = None

    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk.decode('utf-8')

        # extract status and word count once first 2 header lines arrive
        if expected_lines is None:
            first_nl = buffer.find("\n")
            if first_nl != -1:
                second_nl = buffer.find("\n", first_nl + 1)
                if second_nl != -1:
                    status_line = buffer[:first_nl].strip()
                    count_line = buffer[first_nl + 1:second_nl].strip()
                    status_code = status_line.split()[0] if status_line else ""

                    if status_code != "200":
                        expected_lines = 2
                    else:
                        num_words = int(count_line.split()[1])
                        expected_lines = 2 + num_words

        # break when all expected lines have arrived
        if expected_lines is not None and buffer.endswith("\n"):
            if buffer.count("\n") >= expected_lines:
                break

    return buffer

# **********************************
# identical to simple client.py !!!
# **********************************
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
    # ref: https://docs.python.org/3/library/stdtypes.html#str.splitlines
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
    # ref: https://docs.python.org/3/library/stdtypes.html#str.split
    num_words = int(lines[1].split()[1])
    matching_words = lines[2:]

    print(f"Status: {status_line}")
    print(f"Number of matching words: {num_words}")
    print("Matching words:")
    for word in matching_words:
        print(word)

if __name__ == '__main__':
    # tcp client setup connecting to multi-threaded server on port 2222
    serverName = 'localhost'
    serverPort = 2222

    # create TCP stream socket and connect to server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    # need to hold in a loop due to threading; do not want to close loop after first thread finishes
    while True:
        # collect input with at least one '?' or 'quit'
        user_input = collect_user_input()

        if user_input.lower() == "quit":
            # inform server and exit loop
            clientSocket.sendall("QUIT\n".encode('utf-8'))
            break

        # send query to server and receive full response
        response = client_query_server(user_input, clientSocket)

        # parse and display results
        handle_server_response(response)

    # close connection after quitting
    clientSocket.close()
