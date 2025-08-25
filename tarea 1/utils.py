def generate_fault_response(fault_code, fault_string):
    return f"""<?xml version="1.0"?>
<methodResponse>
    <fault>
        <value>
            <struct>
                <member>
                    <name>faultCode</name>
                    <value><int>{fault_code}</int></value>
                </member>
                <member>
                    <name>faultString</name>
                    <value><string>{fault_string}</string></value>
                </member>
            </struct>
        </value>
    </fault>
</methodResponse>
"""

def parse_xml(xml_string):
    import xml.etree.ElementTree as ET
    try:
        return ET.fromstring(xml_string)
    except ET.ParseError:
        return None

def create_response(value):
    return f"""<?xml version="1.0"?>
<methodResponse>
    <params>
        <param>
            <value>{value}</value>
        </param>
    </params>
</methodResponse>
"""