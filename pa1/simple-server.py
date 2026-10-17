from socket import *
import re

def load_wordlist(file_path="wordlist.txt"):
    """
    loads wordlist from file into a list of strings
    returns list of words
    """
    # read words line by line and strip newline whitespace
    words = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            cleaned_word = line.strip()
            if cleaned_word:
                words.append(cleaned_word)
    return words

def find_matching_words(query, words):
    """
    translates wildcard query into regex where '?' matches any character
    and matches anywhere in word (*query*)
    returns list of matching words
    """
    # escape special characters (like '(', ')', '-') to treat them literally
    # ref: https://docs.python.org/3/library/re.html#re.escape:~:text=re%2Eescape%28pattern%29%C2%B6
    escaped_query = re.escape(query)

    # replace escaped '?' with '.' to match any arbitrary character
    regex_pattern = escaped_query.replace(r"\?", ".")

    # compile pattern and search for partial string match across words
    # ref: https://docs.python.org/3/library/re.html#re.search:~:text=re%2Esearch%28pattern%2C%20string%2C%20flags%3D0%29%C2%B6
    pattern = re.compile(regex_pattern)
    return [word for word in words if pattern.search(word)]

def format_server_response(status_code, status_message, matching_words):
    """
    formats response string according to application protocol:
    Line 1: Status Code and Message (i.e. "200 OK")
    Line 2: COUNT <int>
    Line 3+: matching words
    returns formatted response string
    """
    response_lines = [f"{status_code} {status_message}"]
    response_lines.append(f"COUNT {len(matching_words)}")
    for word in matching_words:
        response_lines.append(word)

    # join with newlines and add trailing newline
    return "\n".join(response_lines) + "\n"

def handle_client(connection_socket, words):
    """
    receives query command from client
    performs lookup
    sends response according to application protocol
    """
    # receive request from client
    # ref: https://docs.python.org/3/library/socket.html#socket.socket.recv:~:text=recv%28bufsize%5B%2C%20flags%5D%29%C2%B6
    request = connection_socket.recv(1024).decode('utf-8')
    if not request:
        connection_socket.close()
        return

    # parse command and query string
    request_line = request.strip()
    parts = request_line.split(" ", 1)
    command = parts[0].upper() if len(parts) > 0 else ""

    if command != "QUERY" or len(parts) < 2:
        # invalid command format
        response = format_server_response(400, "BAD REQUEST", [])
    else:
        query_string = parts[1]
        matching_words = find_matching_words(query_string, words)

        if not matching_words:
            response = format_server_response(404, "NOT FOUND", [])
        else:
            response = format_server_response(200, "OK", matching_words)

    # send response back to client and close connection
    connection_socket.sendall(response.encode('utf-8'))
    connection_socket.close()

if __name__ == '__main__':
    # tcp server setup, borrowed from hw3 echo-server.py
    # ref: https://docs.python.org/3/library/socket.html
    serverPort = 12000

    # load wordlist into memory once at startup
    words = load_wordlist("wordlist.txt")
    print(f"Loaded {len(words)} words into memory.")

    # create tcp socket and bind to server port
    # ref: https://docs.python.org/3/library/socket.html#socket.socket.bind:~:text=bind%28address%29%C2%B6
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", serverPort))
    serverSocket.listen(1)

    print("The server is listening. O.O")

    while True:
        # wait for client connection
        connectionSocket, addr = serverSocket.accept()
        print(f"Server connected to {addr}")
        handle_client(connectionSocket, words)
