from flask import Flask, render_template, jsonify, request, url_for
import json
import os

app = Flask(__name__)

# Nombre del archivo JSON
PRODUCTOS_FILE = 'products.json'
WELCOME_FILE = 'welcome.html'

# Función para cargar los productos desde el archivo JSON
def cargar_productos():
    try:
        # Verifica si el archivo existe antes de intentar abrirlo
        if os.path.exists(PRODUCTOS_FILE):
            with open(PRODUCTOS_FILE, 'r', encoding='utf-8') as f:
                productos = json.load(f)
            return productos
        else:
            print(f"Advertencia: El archivo {PRODUCTOS_FILE} no existe. Se devolverá una lista vacía.")
            return []
    except Exception as e:
        print(f"Error al cargar productos desde {PRODUCTOS_FILE}: {e}")
        return []  # En caso de error, devuelve una lista vacía para que la aplicación no se detenga

# Carga los productos al inicio
productos = cargar_productos()

# Define las categorías basadas en los datos del JSON
def obtener_categorias():
    categorias = set()
    # Verifica que la variable global 'productos' esté definida y no sea None
    if productos is not None:
        for producto in productos:
            if "categoria" in producto:  # Verifica si el producto tiene la clave "categoria"
                categorias.add(producto["categoria"])
    return list(categorias)

categorias = obtener_categorias()  # Obtiene la lista de categorías

@app.route("/")
def index():
    """
    Esta ruta renderiza la página de bienvenida (welcome.html)
    """
    return render_template(WELCOME_FILE) # Renderiza welcome.html

@app.route("/home")
def home():
    """
    Esta ruta renderiza la página principal con la lista de productos y categorías.
    """
    productos = cargar_productos()
    categorias = obtener_categorias()
    return render_template("index.html", productos=productos, categorias=categorias)

@app.route("/api/productos", methods=["GET"])
def obtener_productos():
    """
    Esta ruta retorna todos los productos en formato JSON.
    """
    productos = cargar_productos()
    return jsonify(productos)

@app.route("/api/productos", methods=["POST"])
def agregar_producto():
    """
    Esta ruta permite agregar un nuevo producto a la lista.
    """
    nuevo_producto = request.get_json()
    if not nuevo_producto:
        return jsonify({"error": "No se proporcionó un producto en el cuerpo de la solicitud."}), 400

    # Verifica que el nuevo producto tenga los campos requeridos
    campos_requeridos = ["nombre", "precio", "descripcion", "categoria"]
    for campo in campos_requeridos:
        if campo not in nuevo_producto:
            return jsonify({"error": f"Falta el campo requerido: {campo}"}), 400

    try:
        # Carga la lista actual de productos
        productos = cargar_productos()
        # Asigna un nuevo ID basado en la lista actual
        nuevo_producto["id"] = len(productos) + 1
        productos.append(nuevo_producto)

        # Guarda los productos actualizados en el archivo JSON
        with open(PRODUCTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(productos, f, ensure_ascii=False, indent=4)
        return jsonify(nuevo_producto), 201
    except Exception as e:
        return jsonify({"error": f"Error al agregar el producto: {str(e)}"}), 500

@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def actualizar_producto(producto_id):
    """
    Esta ruta permite actualizar un producto existente por su ID.
    """
    producto_actualizado = request.get_json()
    if not producto_actualizado:
        return jsonify({"error": "No se proporcionó un producto en el cuerpo de la solicitud."}), 400

    try:
        # Carga la lista actual de productos
        productos = cargar_productos()

        # Busca el producto a actualizar por su ID
        for i, producto in enumerate(productos):
            if producto["id"] == producto_id:
                # Actualiza los campos del producto
                productos[i].update(producto_actualizado)  # Usa update() para modificar solo los campos proporcionados

                # Guarda los productos actualizados en el archivo JSON
                with open(PRODUCTOS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(productos, f, ensure_ascii=False, indent=4)
                return jsonify(productos[i]), 200  # Devuelve el producto actualizado
        else:
            return jsonify({"error": "Producto no encontrado"}), 404  # Producto no encontrado

    except Exception as e:
        return jsonify({"error": f"Error al actualizar el producto: {str(e)}"}), 500


@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def eliminar_producto(producto_id):
    """
    Esta ruta permite eliminar un producto existente por su ID.
    """
    try:
        # Carga la lista actual de productos
        productos = cargar_productos()

        # Busca el producto a eliminar por su ID
        for i, producto in enumerate(productos):
            if producto["id"] == producto_id:
                # Elimina el producto de la lista
                del productos[i]

                # Guarda los productos actualizados en el archivo JSON
                with open(PRODUCTOS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(productos, f, ensure_ascii=False, indent=4)
                return jsonify({"mensaje": "Producto eliminado correctamente"}), 200
        else:
            return jsonify({"error": "Producto no encontrado"}), 404  # Producto no encontrado

    except Exception as e:
        return jsonify({"error": f"Error al eliminar el producto: {str(e)}"}), 500

@app.route("/categoria/<nombre_categoria>")
def categoria(nombre_categoria):
    """
    Esta ruta maneja la visualización de productos por categoría.
    """
    orden = request.args.get('orden')
    productos_de_categoria = []
    productos = cargar_productos()

    if productos:
        productos_de_categoria = [
            producto for producto in productos if
            "categoria" in producto and producto["categoria"] == nombre_categoria
        ]
    if orden == 'asc':
        productos_de_categoria.sort(key=lambda x: x["precio"])
    elif orden == 'desc':
        productos_de_categoria.sort(key=lambda x: x["precio"], reverse=True)

    if not productos_de_categoria:
        mensaje = f"No hay productos disponibles en la categoría: {nombre_categoria}"
    else:
        mensaje = None
    categorias = obtener_categorias()
    return render_template(
        "index.html",
        productos=productos_de_categoria,
        categorias=categorias,
        categoria_seleccionada=nombre_categoria,
        mensaje=mensaje
    )

@app.route('/buscar', methods=['GET'])
def buscar():
    """
    Esta ruta maneja la búsqueda de productos por nombre y precio.
    """
    query = request.args.get('query', '').lower()
    orden = request.args.get('orden')

    productos_filtrados = []
    productos = cargar_productos()

    if productos:
        if query:
            productos_filtrados = [producto for producto in productos if query in producto["nombre"].lower()]
        else:
            productos_filtrados = productos  # Si no hay query, muestra todos los productos

    # Ordena los productos
    if orden == 'asc':
        productos_filtrados.sort(key=lambda x: x["precio"])
    elif orden == 'desc':
        productos_filtrados.sort(key=lambda x: x["precio"], reverse=True)

    categorias = obtener_categorias()
    mensaje = None # Inicializa mensaje para evitar un error de variable no definida
    return render_template('index.html', productos=productos_filtrados, categorias=categorias,
                           categoria_seleccionada=None, mensaje=mensaje)

if __name__ == "__main__":
    app.run(debug=True)
