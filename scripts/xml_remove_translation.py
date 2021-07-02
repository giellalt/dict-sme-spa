"""
Removes the translated side of an xml dictionary. Configured for the smenob dict.
Usage: python3 {} <PATH_XML_FILE>
Produces the file smespa.xml which can be copied to nds.
"""
import sys
import lxml.etree as etree
from lxml.etree import ElementTree as ET

nodes_to_remove = [
    "xt",
    "x"
]

out_file = "smespa.xml"

# Initial checks before running.
if (len(sys.argv) != 2):
    print("Usage: python3 {} <PATH_XML_FILE>".format(sys.argv[0]))
    exit()

if (sys.argv[1] == "--help" or sys.argv[1] == "-h" or sys.argv[1] == "help"):
    print(__doc__)
    exit()

# Read original file
read_file = sys.argv[1]
# with open(read_file) as f:
#     lines = f.readlines()
#     f.close()

tree = etree.parse(read_file)
for elem in tree.iter():
    #print (elem.tag , elem.attrib)
    if elem.tag in nodes_to_remove:
        elem.getparent().remove(elem)
    if elem.tag == "t":
        elem.text = ""

tree.write(out_file, encoding="UTF-8", pretty_print=True)