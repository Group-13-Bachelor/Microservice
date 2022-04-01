import multiprocessing
import time
def cp():
	while True:
		for i in range(20):
			print('Process: ', i)
		time.sleep(0.05)


x = multiprocessing.Process(target=cp)
x.start()

print("Terminated the child process")