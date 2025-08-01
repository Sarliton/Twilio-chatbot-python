from flask import Flask, jsonify, request
from db import get_db, close_connection, init_db
from qualitor_helpers import login, get_ticket_data, get_tickets
import xml.etree.ElementTree as ET

app = Flask(__name__, static_folder='mobile_interface', static_url_path='/')

app.teardown_appcontext(close_connection)

init_db()

@app.route('/')
def index():
    """Serve the mobile interface."""
    return app.send_static_file('index.html')

@app.route('/api/calls/<client_code>', methods=['GET'])
def list_calls(client_code):
    """Return the latest tickets for a given client."""
    try:
        auth_token = login()
        tickets_response = get_tickets(auth_token, client_code)
        root = ET.fromstring(tickets_response)
        items = root.findall('.//dataitem')
        calls = []
        for item in items:
            calls.append({
                'id': item.find('cdchamado').text,
                'title': item.find('nmtitulochamado').text,
                'created_at': item.find('dtchamado').text if item.find('dtchamado') is not None else None
            })
        return jsonify(calls)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/call/<int:ticket_id>', methods=['GET'])
def call_updates(ticket_id):
    """Return updates for a specific ticket."""
    try:
        auth_token = login()
        updates_response = get_ticket_data(auth_token, ticket_id)
        root = ET.fromstring(updates_response)
        item = root.find('.//dataitem')
        if not item:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        data = {
            'id': item.find('cdchamado').text or 'N/A',
            'title': item.find('nmtitulochamado').text or 'N/A',
            'last_update_date': item.find('dataultimoacompanhamento').text or 'N/A',
            'last_update': item.find('dsultimoacompanhamento').text or 'N/A'
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forms', methods=['POST'])
def create_form():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON esperado'}), 400
    client = data.get('client')
    subject = data.get('subject')
    description = data.get('description')
    if not all([client, subject, description]):
        return jsonify({'error': 'Campos obrigatórios: client, subject, description'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO forms (client, subject, description) VALUES (?, ?, ?)',
                (client, subject, description))
    conn.commit()
    form_id = cur.lastrowid
    return jsonify({'id': form_id, 'message': 'Ficha criada com sucesso'}), 201

@app.route('/api/forms/<int:client>', methods=['GET'])
def list_forms(client):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('SELECT id, subject, description, status, created_at FROM forms WHERE client=?',
                       (client,)).fetchall()
    forms = []
    for row in rows:
        forms.append({
            'id': row[0],
            'subject': row[1],
            'description': row[2],
            'status': row[3],
            'created_at': row[4]
        })
    return jsonify(forms)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
