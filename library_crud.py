from flask import Flask, jsonify, request, session
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
import datetime
from flask_cors import CORS
import bcrypt
import sqlite3
from library_db import Admin, Book
from library_db import get_connection, close_connection
import json


app = Flask(__name__)
app.secret_key = 'rufo'


CORS(app)


### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Seans-Python-Flask-REST-Boilerplate"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)


#registro usuarios




@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Verificar si el usuario ya existe en la base de datos
        if Admin.admin_exists(username):
            return jsonify({'error': 'El usuario ya está registrado.'}), 400
        
        # Generar el hash de la contraseña utilizando bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


        # Crear una instancia de Admin y guardar el administrador
        admin = Admin(username, password)
        if admin.save():
            return jsonify({'message': 'Registro exitoso.'}), 200
        else:
            return jsonify({'error': 'Error al registrar el administrador.'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500



#logueo
@app.route('/login', methods=['POST'])
def login():
    try:
        # Obtener los datos del formulario de inicio de sesión
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Buscar el administrador en la base de datos
        admin = Admin.get_by_username(username)

        if admin and admin.verify_password(password):
            # Establecer la sesión de inicio de sesión para el administrador
            session['admin_id'] = admin.id

            return 'Inicio de sesión exitoso'

        return 'Credenciales inválidas'

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/books', methods=['GET'])
def get_books():
    try:
        title = request.args.get('title')
        author = request.args.get('author')
        category = request.args.get('category')



        # Obtener la lista de libros que coinciden con los parámetros de búsqueda
        if title or author or category:
            books = Book.search(title, author, category)
        else:
            books = Book.get_all()

        if books:
            book_list = []
            for b in books:
                book_data = {
                    'title': b.title,
                    'author': b.author,
                    'availability': b.availability,
                }
                book_list.append(book_data)

            return jsonify(book_list), 200

        return jsonify({'message': 'No books found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#borrar libros
@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si el libro existe antes de eliminarlo
        cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = cursor.fetchone()

        if not book:
            return jsonify({'message': 'Book not found'}), 404

        # Eliminar el libro de la base de datos
        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()

        cursor.close()
        close_connection()

        return jsonify({'message': 'Book deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#agregar libros
@app.route('/books', methods=['POST'])
def add_book():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener los datos del libro del cuerpo de la solicitud
        data = request.get_json()
        title = data.get('title')
        author = data.get('author')
        availability = data.get('availability')

        # Obtener el ID del administrador
        cursor.execute('SELECT id FROM admins LIMIT 1')
        admin_id = cursor.fetchone()[0]

        # Obtener la fecha y hora actual
        created_at = datetime.datetime.now()

        # Agregar el ID del administrador al diccionario de datos
        data['admin_id'] = admin_id

        # Insertar el libro en la base de datos
        cursor.execute('INSERT INTO books (title, author, availability, admin_id, created_at) VALUES (?, ?, ?, ?, ?)',
                    (title, author, availability, admin_id, created_at))
        conn.commit()

        cursor.close()
        close_connection()

        return jsonify({'message': 'Book added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener los nuevos valores del libro del cuerpo de la solicitud
        data = request.get_json()
        title = data.get('title')
        author = data.get('author')
        availability = data.get('availability')

        # Construir la consulta SQL dinámicamente con los campos proporcionados
        query = 'UPDATE books SET '
        parameters = []
        if title:
            query += 'title=?, '
            parameters.append(title)
        if author:
            query += 'author=?, '
            parameters.append(author)
        if availability:
            query += 'availability=?, '
            parameters.append(availability)

        query = query.rstrip(', ') + ' WHERE id=?'
        parameters.append(id)

        # Actualizar los datos del libro en la base de datos
        cursor.execute(query, tuple(parameters))
        conn.commit()

        cursor.close()
        close_connection()

        return jsonify({'message': 'Book updated successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500





if __name__ == '__main__':
    app.run()