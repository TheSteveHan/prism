from server import data_stream
from server.data_filter import operations_callback

data_stream.run("test",operations_callback )
