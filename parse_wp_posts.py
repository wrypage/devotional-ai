import xml.etree.ElementTree as ET
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def parse_wp_xml(xml_path):
    namespaces = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'wp': 'http://wordpress.org/export/1.2/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    }

    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find('channel')

    posts = []

    for item in channel.findall('item'):
        post_type = item.find('wp:post_type', namespaces)
        post_status = item.find('wp:status', namespaces)

        if post_type is None or post_status is None:
            continue

        if post_type.text != 'post' or post_status.text != 'publish':
            continue

        title = item.find('title').text or ''

        content_encoded = item.find('content:encoded', namespaces)
        content_html = content_encoded.text if content_encoded is not None else ''
        content = strip_tags(content_html).strip()

        excerpt_encoded = item.find('excerpt:encoded', namespaces)
        excerpt_html = excerpt_encoded.text if excerpt_encoded is not None else ''
        excerpt = strip_tags(excerpt_html).strip()

        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''

        cats = []
        tags = []
        for cat in item.findall('category'):
            domain = cat.attrib.get('domain')
            if domain == 'category':
                cats.append(cat.text)
            elif domain == 'post_tag':
                tags.append(cat.text)

        link = item.find('link').text if item.find('link') is not None else ''

        posts.append({
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'pub_date': pub_date,
            'categories': cats,
            'tags': tags,
            'post_url': link,
        })

    return posts

if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} wordpress_export.xml")
        sys.exit(1)

    xml_file = sys.argv[1]
    posts = parse_wp_xml(xml_file)

    print(f"Parsed {len(posts)} published blog posts.")

    with open('selah_posts_parsed.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print("Saved parsed posts to selah_posts_parsed.json")
