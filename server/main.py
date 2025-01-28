from server import data_stream
from server.data_filter import operations_callback
from server.settings import app

app.app_context().push()
data_stream.run("test",operations_callback )
