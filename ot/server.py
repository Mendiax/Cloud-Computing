from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import cgi

class FileProcessor:
    """ Class to process files received by the server. """
    def __init__(self, process_function):
        self.process_function = process_function

    def process(self, file_data, filename, message):
        """ Process the file and return the processed filename. """
        return self.process_function(file_data, filename, message)

class HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    """ HTTP Server Request Handler """

    server_version = 'HTTPServer/1.0'

    def __init__(self, *args, file_processor=None, **kwargs):
        self.file_processor = file_processor
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """ Handle POST request sent by the client. """
        if self.path == '/upload':
            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            # Get the file field from the form
            file_field = form['file']
            if file_field.filename:
                # It's a file, process it
                file_data = file_field.file.read()
                file_name = os.path.basename(file_field.filename)

                # Process the file using the provided function
                processed_file_name = self.file_processor.process(file_data, file_name, None)

                # Attempt to read the processed file and send it back
                try:
                    with open(processed_file_name, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition', f'attachment; filename="{processed_file_name}"')
                        self.end_headers()
                        self.wfile.write(f.read())
                except IOError:
                    self.send_error(404, f"File {processed_file_name} not found on server.")
            else:
                # Not a file, error
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No file was uploaded.")
        elif self.path == '/send':
            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            # Check if a message was sent
            if 'message' in form:
                message = form.getvalue('message')
                # Here you could process the text message
                # self.send_response(200)
                # self.end_headers()
                # self.wfile.write(f"Received text message: {message}".encode())
                # Process the file using the provided function
                processed_file_name = self.file_processor.process(None, None, message)

                # Attempt to read the processed file and send it back
                try:
                    with open(processed_file_name, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition', f'attachment; filename="{processed_file_name}"')
                        self.end_headers()
                        self.wfile.write(f.read())
                except IOError:
                    self.send_error(404, f"File {processed_file_name} not found on server.")

            else:
                self.send_error(400, "No message field found.")
        else:
            # Endpoint not found
            self.send_error(404, "Endpoint not found.")

def run_server(process_function, port=8000):
    """ Run the HTTP server """
    def handler(*args, **kwargs):
        HTTPServer_RequestHandler(*args, file_processor=FileProcessor(process_function), **kwargs)

    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    print(f'Server running on port {port}...')
    httpd.serve_forever()

# Example process function that simply returns the same file name for now.
# In reality, this function would process the file and save it with a new name.
def example_process_function(file_data, filename, message):

    if filename is None:
        print(message)
        processed_file_path = 'msg_response.txt'
        import hashlib
        file_data = hashlib.sha1(message.encode()).hexdigest()
        # Here you would add your file processing code
        # For example, save the file_data to the processed_file_path
        with open(processed_file_path, 'w') as f:
            f.write(file_data)
        return processed_file_path
    else:
        processed_file_path = filename + 'response.txt'
        import hashlib
        file_data = hashlib.sha1(file_data).hexdigest()
        # Here you would add your file processing code
        # For example, save the file_data to the processed_file_path
        with open(processed_file_path, 'w') as f:
            f.write(file_data)
        return processed_file_path

if __name__ == '__main__':
    run_server(example_process_function)
