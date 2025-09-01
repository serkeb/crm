import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.customers import customers_bp
from src.routes.contacts import contacts_bp
from src.routes.channels import channels_bp
from src.routes.conversations import conversations_bp
from src.routes.messages import messages_bp
from src.routes.tickets import tickets_bp
from src.routes.automations import automations_bp
from src.routes.templates import templates_bp
from src.routes.reports import reports_bp
from src.routes.webhooks import webhooks_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuración de la aplicación
app.config['SECRET_KEY'] = 'crm-multicanal-secret-key-2024'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-crm-multicanal'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Para desarrollo, en producción usar tiempo limitado

# Configuración de CORS para permitir requests desde el frontend
CORS(app, origins=["*"])

# Configuración de JWT
jwt = JWTManager(app)

# Configuración de SocketIO para notificaciones en tiempo real
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Registro de blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(customers_bp, url_prefix='/api/customers')
app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
app.register_blueprint(channels_bp, url_prefix='/api/channels')
app.register_blueprint(conversations_bp, url_prefix='/api/conversations')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(automations_bp, url_prefix='/api/automations')
app.register_blueprint(templates_bp, url_prefix='/api/templates')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')

# Crear tablas de base de datos
with app.app_context():
    db.create_all()

# Eventos de SocketIO para notificaciones en tiempo real
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    if room:
        from flask_socketio import join_room
        join_room(room)
        print(f'Cliente unido a la sala: {room}')

# Servir archivos estáticos del frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

