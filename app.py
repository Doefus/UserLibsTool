from flask import Flask, request, render_template_string, jsonify
import os
import re
from collections import defaultdict

app = Flask(__name__)

def get_jar_basename(filename):
    match = re.match(r"(.+?)-\d+.*\.jar$", filename)
    return match.group(1) if match else None

@app.route('/', methods=['GET', 'POST'])
def index():
    map_pad = ''
    zoekterm = ''
    bestanden = []
    filter_required = False
    filter_jar = False
    filter_other = False
    show_json_button = False
    show_jar_versions_button = False
    
    if request.method == 'POST':
        map_pad = request.form['map_pad'].replace('\\', '/')
        zoekterm = request.form['zoekterm']
        filter_required = 'filter_required' in request.form
        filter_jar = 'filter_jar' in request.form
        filter_other = 'filter_other' in request.form
        
        if os.path.isdir(map_pad):
            alle_bestanden = os.listdir(map_pad)
            if zoekterm:
                gefilterde_bestanden = [bestand for bestand in alle_bestanden if zoekterm in bestand]
            else:
                gefilterde_bestanden = alle_bestanden

            if filter_required or filter_jar or filter_other:
                bestanden = []
                if filter_required:
                    bestanden.extend([bestand for bestand in gefilterde_bestanden if 'Required' in os.path.splitext(bestand)[1]])
                if filter_jar:
                    bestanden.extend([bestand for bestand in gefilterde_bestanden if bestand.endswith('.jar')])
                if filter_other:
                    bestanden.extend([bestand for bestand in gefilterde_bestanden if not (bestand.endswith('.jar') or 'Required' in os.path.splitext(bestand)[1])])
            else:
                bestanden = gefilterde_bestanden

            # Check if there's at least one .jar file with a related Required file
            jar_files = [bestand for bestand in bestanden if bestand.endswith('.jar')]
            required_files = [bestand for bestand in bestanden if 'Required' in os.path.splitext(bestand)[1]]
            if jar_files and required_files:
                show_json_button = True
            
            # Check if there are at least two .jar files for the jar versions button
            if len(jar_files) >= 2:
                show_jar_versions_button = True
        else:
            bestanden = ['De map bestaat niet.']
    
    return render_template_string(TEMPLATE, bestanden=bestanden, map_pad=map_pad, zoekterm=zoekterm, filter_required=filter_required, filter_jar=filter_jar, filter_other=filter_other, show_json_button=show_json_button, show_jar_versions_button=show_jar_versions_button)

@app.route('/json', methods=['POST'])
def get_json():
    map_pad = request.form['map_pad'].replace('\\', '/')
    zoekterm = request.form['zoekterm']
    filter_required = 'filter_required' in request.form
    filter_jar = 'filter_jar' in request.form
    filter_other = 'filter_other' in request.form
    
    bestanden = []
    if os.path.isdir(map_pad):
        alle_bestanden = os.listdir(map_pad)
        if zoekterm:
            gefilterde_bestanden = [bestand for bestand in alle_bestanden if zoekterm in bestand]
        else:
            gefilterde_bestanden = alle_bestanden

        if filter_required or filter_jar or filter_other:
            bestanden = []
            if filter_required:
                bestanden.extend([bestand for bestand in gefilterde_bestanden if 'Required' in os.path.splitext(bestand)[1]])
            if filter_jar:
                bestanden.extend([bestand for bestand in gefilterde_bestanden if bestand.endswith('.jar')])
            if filter_other:
                bestanden.extend([bestand for bestand in gefilterde_bestanden if not (bestand.endswith('.jar') or 'Required' in os.path.splitext(bestand)[1])])
        else:
            bestanden = gefilterde_bestanden
    
    # Maak de JSON structuur
    bibliotheken = []
    for bestand in bestanden:
        if bestand.endswith('.jar'):
            bibliotheek = {
                "bibliotheek": bestand,
                "modules": []
            }
            jar_name_prefix = os.path.splitext(bestand)[0]
            for module in bestanden:
                if ('Required' in os.path.splitext(module)[1]) and module.startswith(jar_name_prefix):
                    bibliotheek["modules"].append({"module": module})
            bibliotheken.append(bibliotheek)

    return jsonify(bibliotheken)

@app.route('/jar_versions', methods=['POST'])
def get_jar_versions():
    map_pad = request.form['map_pad'].replace('\\', '/')
    zoekterm = request.form['zoekterm']
    
    jar_versions = defaultdict(list)
    if os.path.isdir(map_pad):
        alle_bestanden = os.listdir(map_pad)
        if zoekterm:
            gefilterde_bestanden = [bestand for bestand in alle_bestanden if zoekterm in bestand]
        else:
            gefilterde_bestanden = alle_bestanden

        jar_files = [bestand for bestand in gefilterde_bestanden if bestand.endswith('.jar')]

        for jar in jar_files:
            base_name = get_jar_basename(jar)
            if base_name:
                jar_versions[base_name].append(jar)
        
        # Filter out base names with less than 2 versions
        jar_versions = {k: v for k, v in jar_versions.items() if len(v) > 1}
    
    return jsonify(jar_versions)

TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zoek Bestanden</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css">
    <style>
        body {
            margin: 20px;
        }
        h1, h2 {
            text-align: center;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        form {
            margin-bottom: 20px;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            background: #f4f4f4;
            margin: 5px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .button-primary, .button-json, .button-jar-versions {
            display: inline-block;
            margin: 5px 0;
        }
    </style>
    <script>
        function openJsonInNewTab() {
            var form = document.getElementById('jsonForm');
            var formData = new FormData(form);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/json', true);
            xhr.setRequestHeader('Accept', 'application/json');
            xhr.responseType = 'json';
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var jsonWindow = window.open();
                    jsonWindow.document.write('<pre>' + JSON.stringify(xhr.response, null, 2) + '</pre>');
                }
            };
            xhr.send(formData);
        }
        function openJarVersionsInNewTab() {
            var form = document.getElementById('jarVersionsForm');
            var formData = new FormData(form);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/jar_versions', true);
            xhr.setRequestHeader('Accept', 'application/json');
            xhr.responseType = 'json';
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var jsonWindow = window.open();
                    jsonWindow.document.write('<pre>' + JSON.stringify(xhr.response, null, 2) + '</pre>');
                }
            };
            xhr.send(formData);
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Zoek Bestanden in een Map</h1>
        <form method="post">
            <label for="map_pad">Map Pad:</label>
            <input class="u-full-width" type="text" id="map_pad" name="map_pad" value="{{ map_pad }}" required>
            <br><br>
            <label for="zoekterm">Zoekterm:</label>
            <input class="u-full-width" type="text" id="zoekterm" name="zoekterm" value="{{ zoekterm }}">
            <br><br>
            <label>
                <input type="checkbox" name="filter_required" {% if filter_required %}checked{% endif %}>
                Filter op alle bestanden met 'Required' in de extensie
            </label>
            <br>
            <label>
                <input type="checkbox" name="filter_jar" {% if filter_jar %}checked{% endif %}>
                Filter op .jar bestanden
            </label>
            <br>
            <label>
                <input type="checkbox" name="filter_other" {% if filter_other %}checked{% endif %}>
                Filter op overige bestandstypen
            </label>
            <br><br>
            <button class="button-primary" type="submit">Zoek</button>
            {% if show_json_button %}
            <button class="button-primary button-json" type="button" onclick="openJsonInNewTab()">Toon Resultaten als JSON</button>
            {% endif %}
            {% if show_jar_versions_button %}
            <button class="button-primary button-jar-versions" type="button" onclick="openJarVersionsInNewTab()">Toon .jar dubbelingen</button>
            {% endif %}
        </form>
        <form id="jsonForm" method="post" action="/json" style="display:none;">
            <input type="hidden" name="map_pad" value="{{ map_pad }}">
            <input type="hidden" name="zoekterm" value="{{ zoekterm }}">
            <input type="hidden" name="filter_required" {% if filter_required %}checked{% endif %}>
            <input type="hidden" name="filter_jar" {% if filter_jar %}checked{% endif %}>
            <input type="hidden" name="filter_other" {% if filter_other %}checked{% endif %}>
        </form>
        <form id="jarVersionsForm" method="post" action="/jar_versions" style="display:none;">
            <input type="hidden" name="map_pad" value="{{ map_pad }}">
            <input type="hidden" name="zoekterm" value="{{ zoekterm }}">
        </form>
        <h2>Resultaten:</h2>
        <ul>
            {% for bestand in bestanden %}
                <li>{{ bestand }}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
