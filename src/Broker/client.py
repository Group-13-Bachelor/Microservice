import sys
from Broker import clientAPI


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
    client = clientAPI.Client("tcp://localhost:5555", verbose)
    count = 0
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


    # while count < 10:
    #     request = b"Hello world"
    #     try:
    #         reply = client.send(b"echo", request)
    #     except KeyboardInterrupt:
    #         break
    #     else:
    #         print(f"Reply: {reply}")
    #         # also break on failure to reply:
    #         if reply is None:
    #             break
    #     count += 1
    # print("%i requests/replies processed" % count)


if __name__ == '__main__':
    main()