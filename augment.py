from functools import wraps

def augment(method):
    def wrapper(self,*a,**kw):
        superMethod = getattr(super(self.__class__,self),method.__name__)
        superMethod(*a,**kw)
        method(self,*a,**kw)
    return wraps(method)(wrapper)

def example():
    class A:
        def B(self,i):
            print("A",i)

    class B(A):
        def B(self,i):
            print("B",i)

    class C(A):
        @augment
        def B(self,i):
            print("C",i)

    A().B(1)
    B().B(2)
    C().B(3)


