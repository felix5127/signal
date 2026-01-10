import xml.etree.ElementTree as ET

def parse_opml(file_path):
    """
    Parses an OPML file and returns a list of dictionaries containing feed info.
    """
    feeds = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # OPML 2.0 structure: opml -> body -> outline (can be nested)
        # We'll use a recursive function or findall to get all outlines with xmlUrl
        
        for outline in root.findall('.//outline'):
            xml_url = outline.get('xmlUrl')
            if xml_url:
                feeds.append({
                    'title': outline.get('title') or outline.get('text'),
                    'xmlUrl': xml_url,
                    'type': outline.get('type')
                })
    except Exception as e:
        print(f"Error parsing OPML file {file_path}: {e}")
        
    return feeds
