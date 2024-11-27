import socket
import logging
from contextlib import closing

class RedisClient:
    def __init__(self, host='localhost', port=6379):
        # Initialize the Redis client with the specified host and port
        self.host = host
        self.port = port
        self.socket = None
        self.connect()

    def connect(self):
        # Establish a connection to the Redis server
        try:
            self.socket = socket.create_connection((self.host, self.port))
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm for lower latency
        except socket.error as e:
            logging.error(f"Connection failed: {e}")
            self.socket = None

    def send_command(self, command, *args):
        # Reconnect if the socket is not connected
        if not self.socket:
            self.connect()
        if not self.socket:
            return None

        # Construct and send the command
        command_parts = [command] + list(map(str, args))
        message = f"*{len(command_parts)}\r\n"
        for part in command_parts:
            message += f"${len(part)}\r\n{part}\r\n"  # Add each argument in RESP (REdis Serialization Protocol) format
        logging.debug(f"Sending: {message}")

        try:
            # Send the command to the Redis server
            self.socket.sendall(message.encode('utf-8'))
            return self.read_response()
        except socket.error as e:
            logging.error(f"Socket error: {e}")
            self.socket.close()
            self.socket = None
            return None

    def read_response(self):
        # Read the response from the Redis server
        response = self.read_line()
        if response.startswith('+'):  # Simple string response
            return response[1:]
        elif response.startswith('-'):  # Error response
            raise Exception(f"Error from server: {response[1:]}")
        elif response.startswith(':'):  # Integer response
            return int(response[1:])
        elif response.startswith('$'):  # Bulk string response
            length = int(response[1:])
            if length == -1:
                return None  # Null bulk string
            return self.socket.recv(length + 2)[:-2].decode('utf-8')  # Read the bulk string and remove the trailing CRLF
        elif response.startswith('*'):  # Array response
            count = int(response[1:])
            if count == -1:
                return None  # Null array
            return [self.read_response() for _ in range(count)]  # Recursively read each element of the array
        else:
            raise Exception(f"Unknown response type: {response}")

    def read_line(self):
        # Read a line ending with CRLF from the socket
        line = b''
        while True:
            char = self.socket.recv(1)
            if char == b'\r':
                next_char = self.socket.recv(1)
                if next_char == b'\n':
                    break  # End of line
                else:
                    line += char + next_char
            else:
                line += char
        return line.decode('utf-8')

    def set(self, key, value):
        # Set a key to hold the specified value
        return self.send_command('SET', key, value)

    def get(self, key):
        # Get the value of the specified key
        return self.send_command('GET', key)

    def lpop(self, key):
        # Remove and return the first element of the list stored at the specified key
        return self.send_command('LPOP', key)

    def rpush(self, key, value):
        # Append a value to the list stored at the specified key
        return self.send_command('RPUSH', key, value)

    def select_db(self, db):
        # Select the Redis logical database having the specified zero-based numeric index
        return self.send_command('SELECT', db)

    def close(self):
        # Close the connection to the Redis server
        if self.socket:
            with closing(self.socket):
                self.send_command('QUIT')  # Send the QUIT command to the server
                self.socket = None

    def __del__(self):
        # Ensure the connection is closed when the object is deleted
        self.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    redis_client = RedisClient()
    redis_client.set('foo', 'bar')  # Set key 'foo' to value 'bar'
    value = redis_client.get('foo')  # Get the value of key 'foo'
    print(f"Value for 'foo': {value}")
    redis_client.close()  # Close the connection