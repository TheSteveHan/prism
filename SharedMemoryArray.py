import numpy as np
import multiprocessing.shared_memory as shm
from multiprocessing.resource_tracker import unregister
from multiprocessing import resource_tracker




def remove_shm_from_resource_tracker():
    """Monkey-patch multiprocessing.resource_tracker so SharedMemory won't be tracked

    More details at: https://bugs.python.org/issue38119
    """

    def fix_register(name, rtype):
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.register(self, name, rtype)
    resource_tracker.register = fix_register

    def fix_unregister(name, rtype):
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.unregister(self, name, rtype)
    resource_tracker.unregister = fix_unregister

    if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
        del resource_tracker._CLEANUP_FUNCS["shared_memory"]

class SharedMemoryArray:
    def __init__(self, name, arr=None, dtype=np.float64):
        if name is None:
            raise ValueError("A name must be provided for the shared memory block.")

        self.header_size = 64  # Reserve space for metadata (e.g., dims and shape)
        self.dtype = np.dtype(dtype)
        self.name = name
        if arr is not None:
            shape = arr.shape
            self.shape = shape
            self.itemsize = self.dtype.itemsize
            self.nbytes = np.prod(shape) * self.itemsize

            try:
                # Try to attach to an existing shared memory block
                self.shm = shm.SharedMemory(name=name)
                existing_shape = self._read_header()
                if np.prod(existing_shape) * self.itemsize != self.nbytes:
                    # Existing block is too small, unlink and recreate
                    self.shm.close()
                    self.shm.unlink()
                    self._create_shared_memory(name)
                else:
                    self._initialize_array_from_buf()
            except FileNotFoundError:
                # Shared memory block doesn't exist, create it
                self._create_shared_memory(name)
            self.array[:] = arr
        else:
            self.shm = shm.SharedMemory(name=name)
            existing_shape = self._read_header()
            self._initialize_array_from_buf()

    def _create_shared_memory(self, name):
        """Create a new shared memory block and write the header."""
        self.shm = shm.SharedMemory(create=True, size=self.nbytes + self.header_size, name=name)
        self._write_header()
        self._initialize_array_from_buf()
        self.array.fill(0)  # Initialize to zeros

    def _write_header(self):
        """Write metadata (dims, shape) to the beginning of the buffer."""
        dims = len(self.shape)
        header = np.array([dims] + list(self.shape), dtype=np.int64).tobytes()
        self.shm.buf[:len(header)] = header

    def _read_header(self):
        """Read metadata (dims, shape) from the beginning of the buffer."""
        header = self.shm.buf[:self.header_size]
        header_data = np.frombuffer(header, dtype=np.int64)
        dims = header_data[0]
        shape = tuple(header_data[1:dims + 1])
        return shape

    def _initialize_array_from_buf(self):
        """Initialize the array with the correct offset for shared memory."""
        shape = self._read_header()
        self.array = np.ndarray(shape, dtype=self.dtype, buffer=self.shm.buf[self.header_size:])

    def unlink(self):
        """Unlink and release the shared memory."""
        self.shm.close()
        self.shm.unlink()

    def get_name(self):
        """Get the name of the shared memory block."""
        return self.shm.name

    def get_array(self):
        return self.array

remove_shm_from_resource_tracker()
