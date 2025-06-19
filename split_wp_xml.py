import os
from xml.etree import ElementTree as ET

# === SETTINGS ===
INPUT_FILE = "selah_devotionals.xml"      # Name of your original file
TEMP_FILE = "cleaned_input.xml"           # Temporary cleaned file
CHUNK_SIZE = 200                          # Number of posts per chunk
OUTPUT_DIR = "xml_chunks"                # Output directory

# === CLEANING FUNCTION ===
def clean_invalid_xml_chars(text):
    return ''.join(c for c in text if ord(c) in list(range(32, 127)) or ord(c) in (9, 10, 13))

# === STEP 1: CLEAN FILE ===
with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    raw_xml = f.read()

cleaned_xml = clean_invalid_xml_chars(raw_xml)

with open(TEMP_FILE, "w", encoding="utf-8") as f:
    f.write(cleaned_xml)

# === STEP 2: PARSE CLEANED FILE ===
tree = ET.parse(TEMP_FILE)
root = tree.getroot()

channel = root.find('channel')
header_elements = [e for e in channel if e.tag != 'item']
items = channel.findall('item')

# === STEP 3: SPLIT INTO CHUNKS ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

for i in range(0, len(items), CHUNK_SIZE):
    chunk_items = items[i:i + CHUNK_SIZE]

    chunk_root = ET.Element("rss", root.attrib)
    for prefix, uri in root.attrib.items():
        chunk_root.set(prefix, uri)

    chunk_channel = ET.SubElement(chunk_root, "channel")

    for e in header_elements:
        chunk_channel.append(e)
    for item in chunk_items:
        chunk_channel.append(item)

    chunk_tree = ET.ElementTree(chunk_root)
    chunk_file = os.path.join(OUTPUT_DIR, f"devotionals_part_{i//CHUNK_SIZE + 1}.xml")
    chunk_tree.write(chunk_file, encoding="utf-8", xml_declaration=True)

    print(f"✅ Saved {chunk_file}")

print("\n🎉 Done! Upload the parts when ready.")
