# print("hello")
# print("hello 3")
# mutable and imutable in python:
# mutable elements: int,float,bool,str,tuple,frozenset,byte
# immutable elements list,dict,set,bytearray,custom object --->Instances of classes you define (if attributes are mutable)


def mut(n:int) ->int:
    n +=1
x=2
print(id(x)) # print 11635336
mut(x)
print(x) #output is 2 no difference 

def string_test(string:str)->str:
    string +="add more"
x= "umesh"
string_test(x)
print(x) # output again umesh

#imutable
def imm(x:list) ->list:
    x.append(5)
x = [1,2,3,4]
imm(x)
print(x) #output is [1, 2, 3, 4, 5]

# but if we reassign the element changed doesnt occur:
def reassign(x:list) ->list:
    x = [4,5,6,80]
x = [1,2,3,4]
reassign(x)
print(x) # [1,2,3,4] coz it make a new objet and change doesnt occur

# yes but it is possible in custom mutable elements using class:
from dataclasses import dataclass
# @dataclass
    # @dataclass is a decorator that automatically adds some useful methods to the class:

    # __init__() (constructor)

    # __repr__() (string representation)

    # __eq__() (for comparisons)

    # Others like __hash__() if needed

# The line value: int is a type-annotated class attribute, meaning the class will expect a parameter called value of type int.
#what is decorator in python?
    # A decorator is a function that modifies another function or class without changing its source code. 
    # It adds extra behavior before or after the original function runs.

    # In simple terms:
        # A decorator wraps a function and returns a new one with extra features.
        
    # 🧠 Why use decorators?
    #     Add functionality without changing the function’s code
    #     Code reuse (DRY principle)
    #     Useful in logging, authentication, timing, caching, etc.
    
    # 🎁 Built-in decorators
    #     Decorator	Purpose
    #     @staticmethod	Defines a method without self
    #     @classmethod	Passes class (cls) instead of instance
    #     @property	Makes method behave like an attribute
    # 🔧 Basic Decorator Example
print("decortaor example")
def my_decorator(func):
    def wrapper():
        print("Before function runs")
        func()
        print("After function runs")
    return wrapper

@my_decorator #Decorate the function
def say_hello():#Define the function to decorate
    print("Hello!")

say_hello() # Call the decorated function # output is # Before function runs
                                                    # Hello!
                                                    # After function runs
# how above code works?
    # 🎯Step 1 :Define the decorator
        # def my_decorator(func):
        #     def wrapper():
        #         print("Before function runs")
        #         func()
        #         print("After function runs")
        #     return wrapper
        
        # my_decorator is a function that takes another function (func) as input.
        # Inside it, we define a new function called wrapper() that:
        # Prints before the function runs
        # Calls the original function (func())
        # Prints after it runs
        # It returns this wrapper() function.
        
    # 🎯Step 2: Define the function to decorate
        # def say_hello():
        #     print("Hello!")
    # 🎯 STEP 3: Decorate the function
        # @my_decorator
        # def say_hello():
        #     print("Hello!")
    # this line is exactly same as
    # say_hello = my_decorator(say_hello)
    
    # So what happens?
        #  The function say_hello is passed to my_decorator as the argument func.
        #  my_decorator returns the wrapper function.
        #  Now say_hello points to wrapper, not the original function.
    # 🎯 STEP 4: Call the decorated function
    # 🔁 Visualization:
    # Here’s a simplified flow chart:
        # @my_decorator
        #     ↓
        # say_hello = my_decorator(say_hello)
        #     ↓
        # say_hello()  →  wrapper() → prints "Before"
        #                         → calls original say_hello → prints "Hello!"
        #                         → prints "After"
# 🛠 Decorators with arguments
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):#In Python, _ is a conventional placeholder for a variable whose value you don’t need or care about.
                func(*args, **kwargs)
        return wrapper
    return decorator

@repeat(3)
def greet():
    print("Hi Umesh!")

greet()

print("")
@dataclass
class Umesh:
    value:int

# class Umesh: these both Umesh work as same 
#     def __init__(self, value):
#         self.value = value

def change(x:int) ->int:
    x.value += 15
    
y = Umesh(10)
change(y)
print(y)
# print(y) ---output Umesh() for geting the value need to write y.value if i use __init__(self,value): constructor




