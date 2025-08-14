\
import sys

def add(a, b):
    try:
        return float(a) + float(b)
    except ValueError:
        return "Invalid input: Please enter numbers only."

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python adder.py <number1> <number2>")
    else:
        result = add(sys.argv[1], sys.argv[2])
        print(result)
