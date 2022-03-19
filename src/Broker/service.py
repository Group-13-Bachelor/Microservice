import sys
from Broker import serviceAPI


def main():
    verbose = '-v' in sys.argv
    worker = serviceAPI.Service("tcp://localhost:5555", True)
    reply = None
    worker.subscribe(b"echo")

    while True:
        request = worker.recv()
        if request is None:
            break  # Worker was interrupted
        print(f"service 1 : {request}")

        # worker.reply(b'')


if __name__ == '__main__':
    main()
