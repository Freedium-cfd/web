# cython: language_level=3str

cdef class StringAssignmentMixin:
    def __cinit__(self, str string):
        self.string = str(string) if isinstance(string, StringAssignmentMixin) else string
        self.string_list = list(self.string)

    cdef void __render_string(self):
        self.string = "".join(self.string_list)

    def __len__(self):
        return len(self.string_list)

    cpdef StringAssignmentMixin pop(self, int key):
        self.string_list.pop(key)
        return self

    def encode(self, str encoding):
        self.__render_string()
        return self.string.encode(encoding, "surrogatepass")

    cpdef StringAssignmentMixin insert(self, int key, str value):
        self.string_list.insert(key, value)
        return self

    def __setitem__(self, object key, str value):
        self.string_list[key] = value
        # return self

    def __getitem__(self, object key):
        if isinstance(key, slice):
            return "".join(self.string_list[key])
        else:
            return self.string_list[key]

    def __str__(self):
        self.__render_string()
        return self.string

    __repr__ = __str__

# Make the class available to Python
StringAssignmentMixin_py = StringAssignmentMixin