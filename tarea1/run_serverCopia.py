from serverCopy import Server

if __name__ == "__main__":
    server = Server("127.0.0.1", 8081)
    server.serve()