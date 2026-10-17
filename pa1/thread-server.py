"""
Server side: open a socket on a port, listen for a message from a client,
and send an echo reply; echoes lines until eof when client closes socket;
spawns a thread to handle each client connection; threads share global
memory space with main thread; this is more portable than fork: threads
work on standard Windows systems, but process forks do not;
"""

import time, _thread as thread           # or use threading.Thread().start()
import re
from socket import *                     # get socket constructor and constants
myHost = "localhost"                              # server machine, '' means local host
myPort = 2222                           # listen on a non-reserved port number

sockobj = socket(AF_INET, SOCK_STREAM)           # make a TCP socket object
sockobj.bind((myHost, myPort))                   # bind it to server port number
sockobj.listen(5)                                # allow up to 5 pending connects

# functions here are identical to simple server
# i removed comments for clarity/appearance
# you can view comments for these in simple-server.py
def load_wordlist(file_path="wordlist.txt"):
    words = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            cleaned_word = line.strip()
            if cleaned_word:
                words.append(cleaned_word)
    return words

def find_matching_words(query, words):
    escaped_query = re.escape(query)
    regex_pattern = escaped_query.replace(r"\?", ".")
    pattern = re.compile(regex_pattern)
    return [word for word in words if pattern.search(word)]

def format_server_response(status_code, status_message, matching_words):
    response_lines = [f"{status_code} {status_message}"]
    response_lines.append(f"COUNT {len(matching_words)}")
    for word in matching_words:
        response_lines.append(word)
    return "\n".join(response_lines) + "\n"

# load wordlist once in main thread: ot be shared across spawned threads
words = load_wordlist("wordlist.txt")

def now():
    return time.ctime(time.time())               # current time on the server

def handleClient(connection):                    # in spawned thread: reply
    # time.sleep(5)                              # simulate a blocking activity
    while True:                                  # read, write a client socket
        data = connection.recv(1024)
        if not data: break
        request = data.decode('utf-8').strip()
        if request.upper() == 'QUIT':
            break

        parts = request.split(" ", 1)
        command = parts[0].upper() if len(parts) > 0 else ""

        if command != "QUERY" or len(parts) < 2:
            reply = format_server_response(400, "BAD REQUEST", [])
        else:
            query_string = parts[1]
            matching_words = find_matching_words(query_string, words)
            if not matching_words:
                reply = format_server_response(404, "NOT FOUND", [])
            else:
                reply = format_server_response(200, "OK", matching_words)

        connection.sendall(reply.encode('utf-8'))
    connection.close()

def dispatcher():                                # listen until process killed
    while True:                                  # wait for next connection,
        print("got here")
        connection, address = sockobj.accept()   # pass to thread for service
        print('Server connected by', address, end=' ')
        print('at', now())
        thread.start_new_thread(handleClient, (connection,))

dispatcher()
