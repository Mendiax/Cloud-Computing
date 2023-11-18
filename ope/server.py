from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import cgi

class FileProcessor:
    """ Class to process files received by the server. """
    def __init__(self, process_function):
        self.process_function = process_function

    def process(self, addr, message, payload):
        """ Process the file and return the processed filename. """
        return self.process_function(addr, message, payload)

class HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    """ HTTP Server Request Handler """

    server_version = 'HTTPServer/1.0'

    def __init__(self, *args, file_processor=None, **kwargs):
        self.file_processor = file_processor
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """ Handle POST request sent by the client. """
        if self.path == '/upload' or self.path == '/send':
            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            # print('handle instrcution')
            addr = None
            message = None
            payload = None

            addr = form.getvalue('addr')
            message = form.getvalue('message')
            payload = form.getvalue('payload')


            # try:
            #     # Get the file field from the form
            #     file_field = form['file']
            #     file_data = file_field.file.read()
            #     file_name = os.path.basename(file_field.filename)
            # except:
            #     pass
            # if 'message' in form:
            #     message = form.getvalue('message')

            response = self.file_processor.process(addr, message, payload)
            # Not a file, error
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            # Endpoint not found
            self.send_error(404, "Endpoint not found.")

# Example process function that simply returns the same file name for now.
# In reality, this function would process the file and save it with a new name.
def example_process_function(addr, message, payload):
    # print(addr, message, payload)
    print(f'{addr=}, {message=}, {payload=}')

    return 'return msg'


def run_server(process_function = example_process_function, port=8000):
    """ Run the HTTP server """
    def handler(*args, **kwargs):
        HTTPServer_RequestHandler(*args, file_processor=FileProcessor(process_function), **kwargs)

    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    print(f'Server running on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run_server(example_process_function)
