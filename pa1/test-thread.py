import os
import sys
import time
import socket
import importlib
import subprocess
import pytest
from concurrent.futures import ThreadPoolExecutor

# add current directory to sys.path so we can import thread-client
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# dynamically import thread-client (since filename contains a hyphen)
thread_client = importlib.import_module("thread-client")
client_query_server = thread_client.client_query_server

SERVER_HOST = "localhost"
SERVER_PORT = 2222

def parse_server_response(response_str):
    """
    helper to parse raw response string into (status_code, word_count, word_list)
    """
    lines = response_str.strip().splitlines()
    if not lines:
        return None, 0, []

    status_parts = lines[0].split()
    status_code = int(status_parts[0]) if status_parts and status_parts[0].isdigit() else status_parts[0]

    num_words = 0
    words = []
    if len(lines) > 1 and lines[1].startswith("COUNT"):
        count_parts = lines[1].split()
        if len(count_parts) > 1 and count_parts[1].isdigit():
            num_words = int(count_parts[1])
        words = lines[2:]

    return status_code, num_words, words

def is_server_listening(host, port, timeout=1.0):
    """check if the server is accepting TCP connections"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, ConnectionRefusedError, OSError):
        return False

@pytest.fixture(scope="session", autouse=True)
def start_thread_server():
    """
    session-wide fixture that ensures thread-server.py is running.
    if already running, uses existing server; otherwise starts it as a subprocess.
    """
    server_proc = None
    if not is_server_listening(SERVER_HOST, SERVER_PORT):
        server_path = os.path.join(current_dir, "thread-server.py")
        server_proc = subprocess.Popen([sys.executable, server_path], cwd=current_dir)
        # wait until server is ready to accept connections
        start_time = time.time()
        while time.time() - start_time < 5.0:
            if is_server_listening(SERVER_HOST, SERVER_PORT):
                break
            time.sleep(0.1)

    yield (SERVER_HOST, SERVER_PORT)

    # cleanup server subprocess if we started it
    if server_proc is not None:
        server_proc.terminate()
        server_proc.wait(timeout=2.0)

# ============================================================================
# 1. Required Assignment Test Cases
# ============================================================================

@pytest.mark.parametrize("query, expected_count", [
    ("??????????", 24071),
    ("?", 69903),
    ("?(a)", 414),
    ("-?-", 13),
])
def test_required_assignment_queries(start_thread_server, query, expected_count):
    """
    validates the four exact test cases required by project1.pdf:
    ?????????? -> 24071 matches
    ?          -> 69903 matches
    ?(a)       -> 414 matches
    -?-        -> 13 matches
    """
    host, port = start_thread_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    try:
        response = client_query_server(query, sock)
        status_code, count, words = parse_server_response(response)

        assert status_code == 200
        assert count == expected_count
        assert len(words) == expected_count
    finally:
        sock.sendall(b"QUIT\n")
        sock.close()

# ============================================================================
# 2. Sequential Queries Over a Single Persistent Connection
# ============================================================================

def test_sequential_queries_single_connection(start_thread_server):
    """
    tests that a single client connection can send multiple queries in sequence
    without disconnecting, verifying message framing and persistent state.
    """
    host, port = start_thread_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    try:
        # query 1
        resp1 = client_query_server("-?-", sock)
        code1, count1, words1 = parse_server_response(resp1)
        assert code1 == 200
        assert count1 == 13

        # query 2 on same socket
        resp2 = client_query_server("?(a)", sock)
        code2, count2, words2 = parse_server_response(resp2)
        assert code2 == 200
        assert count2 == 414

        # query 3 on same socket
        resp3 = client_query_server("fry??", sock)
        code3, count3, words3 = parse_server_response(resp3)
        assert code3 == 200
        assert count3 == 3
        assert set(words3) == {"fryer", "frying", "fryingpan"}
    finally:
        sock.sendall(b"QUIT\n")
        sock.close()

# ============================================================================
# 3. Concurrent Multi-threaded Client Requests
# ============================================================================

def test_concurrent_clients(start_thread_server):
    """
    tests that thread-server serves multiple clients simultaneously using threads.
    spawns 4 concurrent client threads and verifies all receive correct answers.
    """
    host, port = start_thread_server

    test_queries = [
        ("-?-", 13),
        ("?(a)", 414),
        ("fry??", 3),
        ("m?tch", 20),
    ]

    def run_single_client(query_and_count):
        query, expected = query_and_count
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        try:
            raw_response = client_query_server(query, sock)
            code, count, words = parse_server_response(raw_response)
            return code == 200 and count == expected and len(words) == expected
        finally:
            sock.sendall(b"QUIT\n")
            sock.close()

    with ThreadPoolExecutor(max_workers=len(test_queries)) as executor:
        results = list(executor.map(run_single_client, test_queries))

    assert all(results), "One or more concurrent client requests failed!"

# ============================================================================
# 4. Error Handling and Edge Cases
# ============================================================================

def test_query_no_matches_404(start_thread_server):
    """
    tests that queries yielding 0 matches return 404 NOT FOUND with COUNT 0.
    """
    host, port = start_thread_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    try:
        # non-existent word pattern
        response = client_query_server("?zzzzzzzzz?", sock)
        code, count, words = parse_server_response(response)
        assert code == 404
        assert count == 0
        assert len(words) == 0
    finally:
        sock.sendall(b"QUIT\n")
        sock.close()

def test_invalid_command_400(start_thread_server):
    """
    tests that an unknown command returns 400 BAD REQUEST.
    """
    host, port = start_thread_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    try:
        sock.sendall(b"INVALID_COMMAND\n")
        raw_response = sock.recv(1024).decode('utf-8')
        code, count, _ = parse_server_response(raw_response)
        assert code == 400
        assert count == 0
    finally:
        sock.sendall(b"QUIT\n")
        sock.close()

def test_immediate_quit(start_thread_server):
    """
    tests connecting and sending QUIT immediately without any queries.
    """
    host, port = start_thread_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(b"QUIT\n")
    # server should close the connection cleanly
    data = sock.recv(1024)
    assert data == b""
    sock.close()

if __name__ == '__main__':
    pytest.main(["-v", __file__])
