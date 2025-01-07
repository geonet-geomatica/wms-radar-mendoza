from flask import Flask, request, Response
from owslib.wms import WebMapService
import requests
from io import BytesIO

app = Flask(__name__)

# Definir la URL base para las imágenes del radar
RADAR_URL = "https://www2.contingencias.mendoza.gov.ar/radar/muestraimagen.php"

@app.route('/wms', methods=['GET'])
def wms():
    # Obtener los parámetros WMS (por ejemplo, BBOX, WIDTH, HEIGHT)
    bbox = request.args.get('BBOX', '-37.40959444444444,-71.71962222222223,-31.22909166666667,-65.02164166666667')
    imagen = request.args.get('imagen', 'google.png')

    # Construir la URL con los parámetros
    url = f"{RADAR_URL}?imagen={imagen}&sw={bbox.split(',')[0]},{bbox.split(',')[1]}&ne={bbox.split(',')[2]},{bbox.split(',')[3]}&centro=-34.0,-68.4&zoom=7"
    
    # Realizar la solicitud HTTP para obtener la imagen
    response = requests.get(url)
    
    # Comprobar si la solicitud fue exitosa
    if response.status_code == 200:
        img = BytesIO(response.content)
        return Response(img, mimetype='image/png')
    else:
        return "Error obteniendo la imagen del radar", 500

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
