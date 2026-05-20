from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_socketio import SocketIO
import sqlite3
import os
from datetime import datetime
from pythonping import ping
import threading
import time

app = Flask(__name__)

app.secret_key = "sistema_escolar"

socketio = SocketIO(app)

UPLOAD_FOLDER = "uploads"
EXAMENES_FOLDER = "examenes"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXAMENES_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["EXAMENES_FOLDER"] = EXAMENES_FOLDER

app.secret_key = "sistema_escolar"

UPLOAD_FOLDER = "uploads"
EXAMENES_FOLDER = "examenes"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXAMENES_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["EXAMENES_FOLDER"] = EXAMENES_FOLDER

# =========================
# CREAR BD
# =========================

def crear_bd():

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS alumnos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        matricula TEXT,

        grupo TEXT,

        estado TEXT,

        ip TEXT,

        conectado TEXT

    )

    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS entregas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT,

        matricula TEXT,

        grupo TEXT,

        archivo TEXT,

        fecha TEXT

    )

    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS examenes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        grupo TEXT,

        archivo TEXT

    )

    """)

    conexion.commit()

    conexion.close()

crear_bd()

# =========================
# MONITOREO RED
# =========================

def monitorear_red():

    while True:

        conexion = sqlite3.connect("database.db")

        cursor = conexion.cursor()

        cursor.execute("""

        SELECT matricula, ip
        FROM alumnos

        """)

        alumnos = cursor.fetchall()

        for alumno in alumnos:

            matricula = alumno[0]
            ip = alumno[1]

            if ip:

                try:

                    respuesta = ping(ip, count=1, timeout=1)

                    if respuesta.success():

                        cursor.execute("""

                        UPDATE alumnos

                        SET conectado=?

                        WHERE matricula=?

                        """,

                        (
                            "Online",
                            matricula
                        ))

                    else:

                        cursor.execute("""

                        UPDATE alumnos

                        SET conectado=?

                        WHERE matricula=?

                        """,

                        (
                            "Offline",
                            matricula
                        ))

                except:

                    cursor.execute("""

                    UPDATE alumnos

                    SET conectado=?

                    WHERE matricula=?

                    """,

                    (
                        "Offline",
                        matricula
                    ))

conexion.commit()

# ENVIAR ACTUALIZACIÓN EN TIEMPO REAL

cursor.execute("""

SELECT * FROM alumnos
ORDER BY grupo

""")

alumnos_actualizados = cursor.fetchall()

socketio.emit(

    "actualizar_monitoreo",

    {

        "alumnos": alumnos_actualizados

    }

)

conexion.close()

time.sleep(5)

# =========================
# INICIAR HILO
# =========================

threading.Thread(
    target=monitorear_red,
    daemon=True
).start()

# =========================
# INICIO
# =========================

@app.route("/")
def inicio():

    return render_template("inicio.html")

# =========================
# LOGIN ALUMNO
# =========================

@app.route("/login_alumno")
def login_alumno():

    return render_template("login_alumno.html")

# =========================
# LOGIN PROFESOR
# =========================

@app.route("/login_profesor")
def login_profesor():

    return render_template("login_profesor.html")

# =========================
# REGISTRO
# =========================

@app.route("/registro")
def registro():

    return render_template("registro.html")

# =========================
# REGISTRAR
# =========================

@app.route("/registrar", methods=["POST"])
def registrar():

    nombre = request.form["nombre"]
    matricula = request.form["matricula"]
    grupo = request.form["grupo"]

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    INSERT INTO alumnos(
        nombre,
        matricula,
        grupo,
        estado,
        ip,
        conectado
    )

    VALUES(?,?,?,?,?,?)

    """,

    (
        nombre,
        matricula,
        grupo,
        "Pendiente",
        "",
        "Offline"
    ))

    conexion.commit()

    conexion.close()

    return redirect("/login_alumno")

# =========================
# ENTRAR ALUMNO
# =========================

@app.route("/entrar_alumno", methods=["POST"])
def entrar_alumno():

    matricula = request.form["matricula"]

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    SELECT * FROM alumnos
    WHERE matricula=?

    """, (matricula,))

    alumno = cursor.fetchone()

    if alumno:

        ip = request.remote_addr

        cursor.execute("""

        UPDATE alumnos

        SET
        ip=?,
        conectado=?

        WHERE matricula=?

        """,

        (
            ip,
            "Online",
            matricula
        ))

        conexion.commit()

        session["matricula"] = matricula

        conexion.close()

        return redirect("/alumno")

    conexion.close()

    return "Alumno no encontrado"

# =========================
# PANEL ALUMNO
# =========================

@app.route("/alumno")
def alumno():

    if "matricula" not in session:

        return redirect("/login_alumno")

    matricula = session["matricula"]

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    SELECT * FROM alumnos
    WHERE matricula=?

    """, (matricula,))

    alumno = cursor.fetchone()

    cursor.execute("""

    SELECT * FROM examenes
    WHERE grupo=?

    ORDER BY id DESC

    """, (alumno[3],))

    examen = cursor.fetchone()

    conexion.close()

    return render_template(
        "alumno.html",
        alumno=alumno,
        examen=examen
    )

# =========================
# LOGIN PROFESOR
# =========================

@app.route("/entrar_profesor", methods=["POST"])
def entrar_profesor():

    usuario = request.form["usuario"]
    password = request.form["password"]

    if usuario == "profesor" and password == "1234":

        session["profesor"] = usuario

        return redirect("/profesor")

    return "Credenciales incorrectas"

# =========================
# DASHBOARD PROFESOR
# =========================

@app.route("/profesor")
def profesor():

    if "profesor" not in session:

        return redirect("/login_profesor")

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    SELECT * FROM alumnos
    ORDER BY grupo

    """)

    alumnos = cursor.fetchall()

    cursor.execute("""

    SELECT * FROM entregas
    ORDER BY id DESC

    """)

    entregas = cursor.fetchall()

    cursor.execute("""

    SELECT * FROM examenes
    ORDER BY id DESC

    """)

    examenes = cursor.fetchall()

    conexion.close()

    return render_template(
        "profesor.html",
        alumnos=alumnos,
        entregas=entregas,
        examenes=examenes
    )

# =========================
# SUBIR EXAMEN
# =========================

@app.route("/subir_examen", methods=["POST"])
def subir_examen():

    grupo = request.form["grupo"]

    archivo = request.files["archivo"]

    if archivo:

        ruta = os.path.join(
            app.config["EXAMENES_FOLDER"],
            archivo.filename
        )

        archivo.save(ruta)

        conexion = sqlite3.connect("database.db")

        cursor = conexion.cursor()

        cursor.execute("""

        INSERT INTO examenes(
            grupo,
            archivo
        )

        VALUES(?,?)

        """,

        (
            grupo,
            archivo.filename
        ))

        conexion.commit()

        conexion.close()

    return redirect("/profesor")

# =========================
# DESCARGAR EXAMEN
# =========================

@app.route("/descargar_examen/<int:id>")
def descargar_examen(id):

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    SELECT * FROM examenes
    WHERE id=?

    """, (id,))

    examen = cursor.fetchone()

    conexion.close()

    return send_from_directory(
        app.config["EXAMENES_FOLDER"],
        examen[2],
        as_attachment=True
    )

# =========================
# SUBIR ENTREGA
# =========================

@app.route("/subir_entrega", methods=["POST"])
def subir_entrega():

    if "matricula" not in session:

        return redirect("/login_alumno")

    archivo = request.files["archivo"]

    matricula = session["matricula"]

    conexion = sqlite3.connect("database.db")

    cursor = conexion.cursor()

    cursor.execute("""

    SELECT * FROM alumnos
    WHERE matricula=?

    """, (matricula,))

    alumno = cursor.fetchone()

    nombre = alumno[1]
    grupo = alumno[3]

    nombre_archivo = archivo.filename

    ruta = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nombre_archivo
    )

    archivo.save(ruta)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    cursor.execute("""

    INSERT INTO entregas(
        nombre,
        matricula,
        grupo,
        archivo,
        fecha
    )

    VALUES(?,?,?,?,?)

    """,

    (
        nombre,
        matricula,
        grupo,
        nombre_archivo,
        fecha
    ))

    cursor.execute("""

    UPDATE alumnos

    SET estado=?

    WHERE matricula=?

    """,

    (
        "Entregado",
        matricula
    ))

    conexion.commit()

    conexion.close()

    return redirect("/alumno")

# =========================
# DESCARGAR ENTREGAS
# =========================

@app.route("/uploads/<filename>")
def uploads(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    if "matricula" in session:

        matricula = session["matricula"]

        conexion = sqlite3.connect("database.db")

        cursor = conexion.cursor()

        cursor.execute("""

        UPDATE alumnos

        SET conectado=?

        WHERE matricula=?

        """,

        (
            "Offline",
            matricula
        ))

        conexion.commit()

        conexion.close()

    session.clear()

    return redirect("/")

# =========================
# EJECUTAR
# =========================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )