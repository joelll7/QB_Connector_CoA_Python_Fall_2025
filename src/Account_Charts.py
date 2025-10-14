import openpyxl
import xml.etree.ElementTree as ET 

def add_account_chart(account_data, xml_root):
    """
    Adds account chart data to the XML root element.
    
    Parameters:
    account_data (list of dict): List containing account chart data.
    xml_root (xml.etree.ElementTree.Element): The root XML element to which account charts will be added.
    """
    for account in account_data:
        account_elem = ET.SubElement(xml_root, 'Account')
        for key, value in account.items():
            child_elem = ET.SubElement(account_elem, key)
            child_elem.text = str(value)
