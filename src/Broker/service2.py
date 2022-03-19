import sys
from Broker import serviceAPI
from time import sleep


def main():
    verbose = '-v' in sys.argv
    worker = serviceAPI.Service("tcp://localhost:5555", True)
    # sleep(1)
    worker.subscribe(b"get_all_post")
    worker.subscribe(b"get_post")
    reply = None
    while True:
        # request = worker.recv()
        with worker.recv() as request:
            if request is None:
                break  # Worker was interrupted
            print(f"service 2 : {request}")
            if request == [b'kill']:
                print("Sleeping")
                sleep(10)
                print("hallo?")
            else:
                worker.reply(request)


if __name__ == '__main__':
    main()
