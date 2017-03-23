import xml.etree.ElementTree as ET

tree = ET.parse('NEH_Grants2010s.xml')
root = tree.getroot()

for grant in root:
    zip = grant.find('InstPostalCode').text


    if state == 'CA' or state == 'ca':
        # print(state)
        print(matching)
        print(outright)
        print(award)
        print()
        ca_total += award
        ca_total_matching += matching
        ca_total_outright += outright

print("Total all", ca_total)
print("Total matching", ca_total_matching)
print("Total outright", ca_total_outright)
