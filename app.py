from flask import Flask, Response, request
from io import BytesIO
from PIL import Image
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bienvenido al servicio WMS de Radar Mendoza"

@app.route('/wms')
def wms():
    # Determinar el tipo de solicitud (GetCapabilities o GetMap)
    request_type = request.args.get('REQUEST', '').upper()

    if request_type == 'GETCAPABILITIES':
        return get_capabilities()
    elif request_type == 'GETMAP':
        return get_map()
    else:
        return Response("Solicitud no válida. Especifique un parámetro REQUEST válido (GetCapabilities o GetMap).", status=400)

def get_capabilities():
    # Respuesta de GetCapabilities
    capabilities = """<?xml version="1.0" encoding="UTF-8"?>
    <WMS_Capabilities xmlns:xlink="http://www.w3.org/1999/xlink" version="1.3.0">
        <Service>
            <Name>WMS</Name>
            <Title>Radar Mendoza</Title>
            <Abstract>Servicio WMS para mostrar radar de Mendoza</Abstract>
            <KeywordList>
                <Keyword>Radar</Keyword>
                <Keyword>Mendoza</Keyword>
            </KeywordList>
            <OnlineResource xlink:type="simple" xlink:href="https://wms-radar-mendoza.onrender.com/wms" />
        </Service>
        <Capability>
            <Request>
                <GetCapabilities>
                    <Format>application/xml</Format>
                </GetCapabilities>
                <GetMap>
                    <Format>image/png</Format>
                    <DCPType>
                        <HTTP>
                            <Get>
                                <OnlineResource xlink:type="simple" xlink:href="https://wms-radar-mendoza.onrender.com/wms" />
                            </Get>
                        </HTTP>
                    </DCPType>
                </GetMap>
            </Request>
            <Layer>
                <Title>Radar Mendoza</Title>
                <Abstract>Datos de radar de la provincia de Mendoza</Abstract>
                <CRS>EPSG:4326</CRS>
                <BoundingBox CRS="EPSG:4326" minx="-71.7249353229" miny="-37.4356023471" maxx="-64.9942298547" maxy="-31.2320003192" />
                <Layer queryable="1">
                    <Name>radar</Name>
                    <Title>Radar Mendoza</Title>
                </Layer>
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    # Verificar parámetros necesarios para GetMap
    bbox = request.args.get('BBOX')
    width = request.args.get('WIDTH')
    height = request.args.get('HEIGHT')
    crs = request.args.get('CRS')
    format_ = request.args.get('FORMAT')

    # Validar parámetros
    if not all([bbox, width, height, crs, format_]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    try:
        # Parsear parámetros de BBOX
        minx, miny, maxx, maxy = map(float, bbox.split(','))
        width = int(width)
        height = int(height)

        # Registrar los parámetros recibidos para depuración
        print(f"BBOX: {bbox}, WIDTH: {width}, HEIGHT: {height}, CRS: {crs}, FORMAT: {format_}")

        # URL de la imagen del radar
        img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

        # Recuperar la imagen del radar
        img_response = requests.get(img_url)
        img_response.raise_for_status()

        # Abrir la imagen
        img = Image.open(BytesIO(img_response.content))

        # Dimensiones del área del radar (coordenadas geográficas)
        radar_minx, radar_miny = -71.7249353229, -37.4356023471  # Esquina inferior izquierda
        radar_maxx, radar_maxy = -64.9942298547, -31.2320003192  # Esquina superior derecha

        # Calcular las posiciones del recorte en píxeles
        radar_width, radar_height = img.size

        # Calcular las coordenadas del recorte (en píxeles)
        left = int((minx - radar_minx) / (radar_maxx - radar_minx) * radar_width)
        top = int((maxy - radar_maxy) / (radar_miny - radar_maxy) * radar_height)
        right = int((maxx - radar_minx) / (radar_maxx - radar_minx) * radar_width)
        bottom = int((miny - radar_maxy) / (radar_miny - radar_maxy) * radar_height)

        # Asegurarse de que las coordenadas estén dentro de los límites de la imagen
        left = max(0, min(left, radar_width))
        top = max(0, min(top, radar_height))
        right = max(0, min(right, radar_width))
        bottom = max(0, min(bottom, radar_height))

        # Recortar la imagen usando las coordenadas calculadas
        cropped_img = img.crop((left, top, right, bottom))

        # Escalar la imagen al tamaño solicitado
        scaled_img = cropped_img.resize((width, height), Image.ANTIALIAS)

        # Convertir la imagen a PNG
        img_io = BytesIO()
        scaled_img.save(img_io, 'PNG')
        img_io.seek(0)

        # Crear la respuesta con la imagen escalada
        response = Response(img_io.getvalue(), content_type='image/png')
        response.headers['Content-Disposition'] = 'inline; filename="radar.png"'

        return response
    except Exception as e:
        # Registrar el error para depuración
        print(f"Error al procesar GetMap: {str(e)}")
        return Response(f"Error al procesar la solicitud de mapa: {str(e)}", status=500)

if __name__ == "__main__":
    # Utilizamos el puerto de la variable de entorno o el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)






