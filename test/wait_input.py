import sys


while(True):
    print("Waiting for output")
    sys.stdout.flush()
    val = input()
    print("Received input {}, continuing".format(val))
