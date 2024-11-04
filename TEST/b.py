from functions.func import func2

class B:
    def __init__(self):
        self.var2 = 1
        self.var3 = 1
        self.var4 = 1
        self.var5 = func2(self.var5)
        print("B.var5", self.var5)


class E:
    def __init__(self):
        self.var = 10

print("imported b.py")        