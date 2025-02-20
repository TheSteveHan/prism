# https://docs.gunicorn.org/en/latest/settings.html

# https://docs.gunicorn.org/en/latest/settings.html#server-socket
# bind = "0.0.0.0:8040"

# https://docs.gunicorn.org/en/latest/settings.html#worker-processes
# looking to reserve memory... so making this multi-threaded instead of multi-process
workers = 1
threads = 5

