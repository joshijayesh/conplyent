from pyosexec import console_executor


c = console_executor.ConsoleExecutor("python test/paused_multiple_output.py")

for i in c.read_output(timeout=1):
    if(i is None):
        c.send_input("This is an intervention")
    else:
        print(i)
