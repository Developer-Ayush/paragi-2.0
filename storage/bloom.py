import mmh3
from bitarray import bitarray
import math
import os

class BloomFilter:
    def __init__(self, capacity: int, error_rate: float):
        self.capacity = capacity
        self.error_rate = error_rate
        self.bit_size = int(-(capacity * math.log(error_rate)) / (math.log(2) ** 2))
        self.hash_count = int((self.bit_size / capacity) * math.log(2))
        self.bit_array = bitarray(self.bit_size)
        self.bit_array.setall(0)

    def add(self, key: str):
        for i in range(self.hash_count):
            index = mmh3.hash(key, i) % self.bit_size
            self.bit_array[index] = 1

    def __contains__(self, key: str) -> bool:
        for i in range(self.hash_count):
            index = mmh3.hash(key, i) % self.bit_size
            if not self.bit_array[index]:
                return False
        return True

    def save(self, path: str):
        with open(path, 'wb') as f:
            self.bit_array.tofile(f)

    def load(self, path: str):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.bit_array = bitarray()
                self.bit_array.fromfile(f)
                # Ensure it matches the expected size
                if len(self.bit_array) != self.bit_size:
                    # Handle size mismatch if necessary
                    new_bit_array = bitarray(self.bit_size)
                    new_bit_array.setall(0)
                    min_len = min(len(self.bit_array), self.bit_size)
                    new_bit_array[:min_len] = self.bit_array[:min_len]
                    self.bit_array = new_bit_array
