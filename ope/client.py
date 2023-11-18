import threading
import time
import requests

def send_message_to_server(url, addr, message, payload=None):
    """
    Send a text message to the HTTP server and print the server's response.

    @param message The text message to be sent.
    @param url The URL of the server endpoint expecting the text message.
    """
    print(f'client sends to {addr} {message=}')
    url += '/send'
    data = {
        'addr' : addr,
        'message': message,
        'payload' : payload
    }
    print(f'clients sends {data=}')
    response = requests.post(url, data=data)
    return response.content.decode()
    # try:
    #     response = requests.post(url, data=data)
    #     print(f"Server Response: {response.content}")
    # except requests.exceptions.RequestException as e:
    #     print(f"An error occurred: {e}")


if __name__ == "__main__":
    import sys
    # Replace with the path to the file you wish to send
    import server
    def run_server():
        server.run_server()

    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    time.sleep(2)
    print('client:')

    # URL of the server endpoint, change the port if needed
    server_url = 'http://localhost:8000/'

    print(send_message_to_server(server_url, addr='1of2',message='test_msg',payload='xddd'))

