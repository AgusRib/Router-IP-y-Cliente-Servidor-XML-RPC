from client2 import Client

def main():
    # Create and connect client
    client = Client()
    client.connect("127.0.0.1", 12000)
    
    try:
        result = client.suma(5, 3)
        print(f"Result of suma(5, 3): {result}")
        client.connect("127.0.0.1", 12000)
        # Test with different numbers
        result2 = client.suta(10, 20)
        print(f"Result of suma(10, 20): {result2}")
        
    except Exception as e:
        print(f"Error testing client: {e}")

if __name__ == "__main__":
    main()