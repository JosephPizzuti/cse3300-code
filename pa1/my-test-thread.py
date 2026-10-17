from socket import *
import importlib

# import client query function from thread-client.py
thread_client = importlib.import_module("thread-client")
client_query_server = thread_client.client_query_server

serverName = 'localhost'
serverPort = 2222

test_cases = [
    ("??????????", 24071),
    ("?", 69903),
    ("?(a)", 414),
    ("-?-", 13),
]

def test_simple_queries():
    # connect once to multi-threaded server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    print(f"\nConnected to thread-server at {serverName}:{serverPort}\n")

    all_passed = True

    for query, expected_count in test_cases:
        print(f"Testing Query: {query}")

        # send query and receive complete response
        response = client_query_server(query, clientSocket)
        lines = response.strip().splitlines()

        # extract status code and word count from response header
        status_line = lines[0]
        actual_count = int(lines[1].split()[1])

        print(f"Server Status: {status_line}")
        print(f"Expected Count: {expected_count}")
        print(f"Actual Count: {actual_count}")

        if status_line == "200 OK" and actual_count == expected_count:
            print("--- Result: PASS ---\n")
        else:
            print("--- Result: FAIL ---\n")
            all_passed = False

    # send quit command and close connection
    clientSocket.sendall(b"QUIT\n")
    clientSocket.close()

    assert all_passed, "One or more simple queries failed to match expected count!"
    print("All 4 test cases PASSED successfully!")

if __name__ == '__main__':
    test_simple_queries()
