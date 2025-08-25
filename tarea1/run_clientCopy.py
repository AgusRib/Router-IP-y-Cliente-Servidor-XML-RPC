from clientCopy import Client

if __name__ == "__main__":
    client = Client()
    client.connect("127.0.0.1", 8081)
    client.andar()