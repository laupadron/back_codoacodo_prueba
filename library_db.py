import sqlite3
import bcrypt


from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
CORS(app)
DATABASE = 'library.db'
conn = None

def get_connection():
    global conn
    if conn is None:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
    return conn

def close_connection():
    global conn
    if conn is not None:
        conn.close()
        conn = None
        


# def connection():
#     conn = sqlite3.connect(DATABASE)
#     conn.row_factory = sqlite3.Row
#     return conn

#creo las tablas

def create_tables():
    global conn
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR NOT NULL,
            author VARCHAR NOT NULL,
            availability VARCHAR NOT NULL,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books_categories (
            book_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL
    
        )   
    ''')




    
    cursor.close()


    

#class book

class Book:
    def __init__(self, title, author, availability):
        self.title = title
        self.author = author
        self.availability = availability

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO books (title, author, availability)
                VALUES (?, ?, ?)
            ''', (self.title, self.author, self.availability))

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print("Error:", e)
        finally:
            cursor.close()

    def insert_book(title, author, availability):
        book = Book(title, author, availability)
        book.save()

    @staticmethod
    def search(title=None, author=None, category=None):
        # Lógica de búsqueda con los parámetros proporcionados (title, author, category)
        # Devuelve una lista de objetos Book que coinciden con los criterios de búsqueda

        # Conectarse a la base de datos
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM books WHERE 1=1'
            parameters = []

            if title:
                query += ' AND title LIKE ?'
                parameters.append('%' + title + '%')

            if author:
                query += ' AND author LIKE ?'
                parameters.append('%' + author + '%')

            if category:
                query += '''
                    AND EXISTS (
                        SELECT 1
                        FROM books_categories AS bc
                        INNER JOIN categories AS c ON bc.category_id = c.id
                        WHERE bc.book_id = books.id
                        AND c.name LIKE ?
                    )
                '''
                parameters.append('%' + category + '%')

            # Ejecutar la consulta SQL con los parámetros
            cursor.execute(query, parameters)
            books_data = cursor.fetchall()

            # Crear una lista de objetos Book con los datos obtenidos
            books = []
            for book_data in books_data:
                book = Book(book_data[1], book_data[2], book_data[3])
                books.append(book)

            return books

        except sqlite3.Error as e:
            print("Error:", e)
            return []

        finally:
            cursor.close()
            close_connection()

    @staticmethod
    def get_all():
        # Lógica para obtener todos los libros de la base de datos
        # Devuelve una lista de objetos Book con todos los libros

        # Conectarse a la base de datos
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Obtener todos los libros de la tabla books
            cursor.execute('SELECT * FROM books')
            books_data = cursor.fetchall()

            # Crear una lista de objetos Book con los datos obtenidos
            books = []
            for book_data in books_data:
                book = Book(book_data[1], book_data[2], book_data[3])
                books.append(book)

            return books

        except sqlite3.Error as e:
            print("Error:", e)
            return []

        finally:
            cursor.close()
            close_connection()

        
        

   

#class categories

class Category:
    def __init__(self, name):
        self.name = name

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO categories (name)
                VALUES (?)
            ''', (self.name,))

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print("Error:", e)
        finally:
            cursor.close()

def insert_category(name):
    category = Category(name)
    category.save()


#class book_categories
class BookCategory:
    def __init__(self, book_id, category_id):
        self.book_id = book_id
        self.category_id = category_id

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO books_categories (book_id, category_id)
                VALUES (?, ?)
            ''', (self.book_id, self.category_id))

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print("Error:", e)
        finally:
            cursor.close()

def insert_book_categories(book_id, category_id):
    book_category = BookCategory(book_id, category_id)
    book_category.save()


#class admin


class Admin:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Generar el hash de la contraseña utilizando bcrypt
            password_hash = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt())

            cursor.execute('''
                INSERT INTO admins (username, password)
                VALUES (?, ?)
            ''', (self.username, password_hash))

            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print("Error:", e)
            return False
        finally:
            cursor.close()

    @classmethod
    def admin_exists(cls, username):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM admins WHERE username=?', (username,))
        count = cursor.fetchone()[0]

        cursor.close()
        close_connection()

        return count > 0
    
    @classmethod
    def get_by_username(cls, username):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, username, password FROM admins WHERE username=?', (username,))
        admin_data = cursor.fetchone()

        if admin_data:
            admin_id, admin_username, admin_password = admin_data
            admin = cls(admin_username, admin_password)
            admin.id = admin_id
            return admin

        return None

    def verify_password(self, password):
        hashed_password = self.password
        return bcrypt.checkpw(password.encode(), hashed_password)
            # close_connection()

def insert_admins(username, password):
    admin = Admin(username, password)
    admin.save()







if __name__ == '__main__':
    create_tables()

if __name__ == '__main__':
#     insert_book("Antología poética", "Marechal, Leopoldo", "Available")
#     insert_book("De mala muerte", "Abós, Álvaro", "Available")
#     insert_book("Confesiones", "Agustín, Santo", "Not Available")
#     insert_category("Poesía")
#     insert_category("Cuento")
#     insert_category("Novela")
#     insert_admins("laupadron","hola1234")
    



        


# Obtener los IDs de los libros y categorías recién insertados
    
    conn = get_connection()
    cursor = conn.cursor()



    cursor.execute('SELECT id FROM books WHERE title = ?', ("Antología poética",))
    book_id_1 = cursor.fetchone()[0]


    cursor.execute('SELECT id FROM books WHERE title = ?', ("De mala muerte",))
    book_id_2 = cursor.fetchone()[0]

    cursor.execute('SELECT id FROM books WHERE title = ?', ("Confesiones",))
    book_id_3 = cursor.fetchone()[0]


    cursor.execute('SELECT id FROM categories WHERE name = ?', ("Poesía",))
    category_id_1 = cursor.fetchone()[0]


    cursor.execute('SELECT id FROM categories WHERE name = ?', ("Cuento",))
    category_id_2 = cursor.fetchone()[0]

    cursor.execute('SELECT id FROM categories WHERE name = ?', ("Novela",))
    category_id_3 = cursor.fetchone()[0]


# conn.commit()
    cursor.close()
    close_connection()

#Agregar la relación entre libros y categorías en la tabla pivote
# insert_book_categories(book_id_1, category_id_1)
# insert_book_categories(book_id_2, category_id_2)
# insert_book_categories(book_id_3, category_id_3)

