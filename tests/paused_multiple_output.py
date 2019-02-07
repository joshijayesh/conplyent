import time
import sys

for i in range(0, int(sys.argv[1])):
    print("Some random text + {}".format(sys.argv[2]))
    sys.stdout.flush()
    time.sleep(float(sys.argv[3]))
