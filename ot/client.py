import requests

def send_file_to_server(file_path, url):
    """
    Send a file to the HTTP server and print the server's response.

    @param file_path The path to the file to be sent.
    @param url The URL of the server endpoint expecting the file upload.
    """
    url += "/upload"
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f)}
        response = requests.post(url, files=files)
        return response.content
        # try:
        #     response = requests.post(url, files=files)
        #     print(f"Server Response: {response.text}")
        #     print(f"Server Response: {response.headers}")


        # except requests.exceptions.RequestException as e:
        #     print(f"An error occurred: {e}")

def send_message_to_server(message, url):
    """
    Send a text message to the HTTP server and print the server's response.

    @param message The text message to be sent.
    @param url The URL of the server endpoint expecting the text message.
    """
    url += '/send'
    data = {'message': message}
    response = requests.post(url, data=data)
    return response.content
    # try:
    #     response = requests.post(url, data=data)
    #     print(f"Server Response: {response.content}")
    # except requests.exceptions.RequestException as e:
    #     print(f"An error occurred: {e}")


if __name__ == "__main__":
    import sys
    # Replace with the path to the file you wish to send
    file_path_to_send = sys.argv[1]

    # URL of the server endpoint, change the port if needed
    server_url = 'http://localhost:8000/'

    print(send_file_to_server(file_path_to_send, server_url))
    print("--------------------------------------------------")
    print(send_message_to_server(file_path_to_send, server_url))

