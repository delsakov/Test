from b import B
import functions
#from functions.func import *

class A(B):
    def __init__(self):
        self.var = 1
        self.var2 = functions.func.func1(self.var)
        print("A.var2", self.var2)


class C:
    def __init__(self):
        self.var = 2
        self.var2 = functions.func.func1(self.var)
        print("C.var2", self.var2)


class D:
    def __init__(self):
        self.var = 2


aa = A()
cc = C()
dd = D()
