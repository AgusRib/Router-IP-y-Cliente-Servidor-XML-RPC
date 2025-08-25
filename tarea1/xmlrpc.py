class XMLRPCProtocol:
    def marshal(self, method_name, params):
        # Convert the method name and parameters to XML-RPC format
        xml = f"""<?xml version="1.0"?>
<methodCall>
    <methodName>{method_name}</methodName>
    <params>"""
        for param in params:
            xml += f"""
        <param>
            <value>{self._to_xml_value(param)}</value>
        </param>"""
        xml += """
    </params>
</methodCall>"""
        return xml

    def _to_xml_value(self, value):
        # Convert Python values to XML-RPC compatible XML
        if isinstance(value, int):
            return f"<int>{value}</int>"
        elif isinstance(value, float):
            return f"<double>{value}</double>"
        elif isinstance(value, str):
            return f"<string>{value}</string>"
        elif isinstance(value, list):
            return "<array><data>" + "".join(f"<value>{self._to_xml_value(v)}</value>" for v in value) + "</data></array>"
        elif isinstance(value, dict):
            return "<struct>" + "".join(f"<member><name>{k}</name><value>{self._to_xml_value(v)}</value></member>" for k, v in value.items()) + "</struct>"
        else:
            raise ValueError("Unsupported type for XML-RPC")

    def unmarshal(self, xml):
        # Parse the XML-RPC response and extract the result
        # This is a simplified example; a full implementation would require proper XML parsing
        if "<fault>" in xml:
            return self._parse_fault(xml)
        else:
            return self._parse_response(xml)

    def _parse_fault(self, xml):
        # Extract fault code and string from the XML
        fault_code = self._extract_value(xml, "faultCode")
        fault_string = self._extract_value(xml, "faultString")
        return {"faultCode": fault_code, "faultString": fault_string}

    def _parse_response(self, xml):
        # Extract the result from the XML
        return self._extract_value(xml, "value")

    def _extract_value(self, xml, tag):
        # Extract the value of a specific tag from the XML
        start = xml.find(f"<{tag}>") + len(tag) + 2
        end = xml.find(f"</{tag}>")
        return xml[start:end] if start > -1 and end > -1 else None

class XMLRPCServer:
    def __init__(self, address):
        self.address = address
        self.methods = {}

    def add_method(self, method):
        self.methods[method.__name__] = method

    def serve(self):
        # Start the server and listen for incoming requests
        import socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.address)
        server_socket.listen(5)
        while True:
            client_socket, _ = server_socket.accept()
            self.handle_request(client_socket)

    def handle_request(self, client_socket):
        # Handle incoming XML-RPC requests
        request = client_socket.recv(1024).decode()
        method_name, params = self._parse_request(request)
        response = self._execute_method(method_name, params)
        client_socket.sendall(response.encode())
        client_socket.close()

    def _parse_request(self, request):
        # Extract method name and parameters from the request
        # This is a simplified example; a full implementation would require proper XML parsing
        return "methodName", ["param1", "param2"]

    def _execute_method(self, method_name, params):
        if method_name in self.methods:
            try:
                result = self.methods[method_name](*params)
                return f"<methodResponse><params><value>{result}</value></params></methodResponse>"
            except Exception as e:
                return self._fault_response(4, str(e))  # Internal error
        else:
            return self._fault_response(2, "Method not found")  # Method not found

    def _fault_response(self, fault_code, fault_string):
        return f"<methodResponse><fault><value><struct><member><name>faultCode</name><value><int>{fault_code}</int></value></member><member><name>faultString</name><value><string>{fault_string}</string></value></member></struct></value></fault></methodResponse>"