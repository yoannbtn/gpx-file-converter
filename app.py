import os
from flask import Flask, request, send_file, render_template
import tempfile
from lxml import etree

app = Flask(__name__)

# Dictionnaires pour les codes de couleur et les préfixes des noms
color_codes = {
    "Red": 0,
    "Yellow": 1,
    "Green": 2,
    "Blue": 3,
    "Purple": 4,
    "Black": 5,
    "Brown": 6
}

name_prefixes = {
    "CN": "Blue",
    "CW": "Blue",
    "CE": "Blue",
    "CS": "Blue",
    "LB": "Red",
    "LT": "Green",
    "MS": "Yellow",
    "D": "Purple"
}

def get_color_code(name):
    for prefix, color in name_prefixes.items():
        if name.startswith(prefix):
            return color_codes[color]
    return color_codes["Black"]  # Default color if no prefix matches

def get_gp39symbol(name):
    if name.startswith("D"):
        return '8'
    return '1'

def convert_gpx(input_file):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(input_file, parser)
    root = tree.getroot()
    
    # Remove default namespace
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'): continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    
    # Create a new root for the output GPX
    nsmap = {
        None: 'http://www.topografix.com/GPX/1/1',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsd': 'http://www.w3.org/2001/XMLSchema'
    }
    new_root = etree.Element('gpx', nsmap=nsmap, version='1.1')

    # Process each waypoint
    for wpt in root.findall('wpt'):
        lat = wpt.get('lat')
        lon = wpt.get('lon')
        name_element = wpt.find('name')
        
        if name_element is not None:
            name = name_element.text
            new_wpt = etree.SubElement(new_root, 'wpt', {'lat': lat, 'lon': lon})
            etree.SubElement(new_wpt, 'name').text = name

            extensions = etree.SubElement(new_wpt, 'extensions')
            
            # Fixed values with the new rule for GP39Symbol
            etree.SubElement(extensions, 'GP39Symbol').text = get_gp39symbol(name)
            etree.SubElement(extensions, 'FECColor').text = str(get_color_code(name))
            etree.SubElement(extensions, 'GP39Comment').text = '1'
            etree.SubElement(extensions, 'GP39Flag').text = '1'

    # Write the new tree to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".gpx")
    new_tree = etree.ElementTree(new_root)
    new_tree.write(temp_file.name, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    temp_file.close()
    return temp_file.name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    output_file_path = convert_gpx(file)
    
    return send_file(output_file_path, as_attachment=True, download_name='converted.gpx')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
