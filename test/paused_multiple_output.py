import time
import sys

for i in range(0, 15):
    print("Some random text + {}".format(sys.argv[1]))
    sys.stdout.flush()
    time.sleep(0.2)
