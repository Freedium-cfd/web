cdef class StringAssignmentMixin:
    cdef:
        str string
        list string_list

    cdef void __render_string(self)

    cpdef StringAssignmentMixin pop(self, int key)
    cpdef StringAssignmentMixin insert(self, int key, str value)
