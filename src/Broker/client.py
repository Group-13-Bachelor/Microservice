import sys
from common import clientAPI


# def main():
#     # verbose = '-v' in sys.argv
#     client = clientAPI.Client("tcp://localhost:5555", True)
#
#     request = b"Hello world"
#     client.send(b"echo", request)
#
#     reply = client.recv()
#     print(f"Reply: {reply}")
#
#
#
# if __name__ == '__main__':
#     main()


def main():
    verbose = '-v' in sys.argv
    client = clientAPI.Producer("tcp://localhost:5555", True)
    while True:
        try:
            message = input("Message: ")
        except KeyboardInterrupt:
            print(f"KeyboardInterrupt")
            break
        # client.send(b"echo", message.encode('utf-8'))
        client.send(b"echo", message.encode('utf-8'))
        reply = client.recv()
        print(f"Reply from Service: {reply}")





if __name__ == '__main__':
    main()
