from flask import Flask, Response, request
from io import BytesIO
from PIL import Image
import requests
import os
from pyproj import Transformer

app = Flask(__name__)

# Coordenadas de la imagen base (EPSG:3857)
ORIGIN_X = -68.25000000000001
ORIGIN_Y = -34.24966653449996
PIXELS_PER_UNIT = 152.87405654296876  # Corresponde al nivel 10
IMAGE_WIDTH = 256
IMAGE_HEIGHT = 256

@app.route('/')
def index():
    return "Bienvenido al servicio WMS de Radar Mendoza"

@app.route('/wms')
def wms():
    request_type = request.args.get('REQUEST', '').upper()
    if request_type == 'GETCAPABILITIES':
        return get_capabilities()
    elif request_type == 'GETMAP':
        return get_map()
    else:
        return Response("Solicitud no válida. Especifique un parámetro REQUEST válido (GetCapabilities o GetMap).", status=400)

def get_capabilities():
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
                <CRS>EPSG:3857</CRS>
                <BoundingBox CRS="EPSG:3857" minx="-68.25000000000001" miny="-34.24966653449996" maxx="-67.75032747733738" maxy="-33.74999999999999" />
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    # Parámetros requeridos
    bbox = request.args.get('BBOX')
    width = int(request.args.get('WIDTH', 256))
    height = int(request.args.get('HEIGHT', 256))
    crs = request.args.get('CRS', 'EPSG:3857')
    format_ = request.args.get('FORMAT', 'image/png')

    if not all([bbox, width, height, crs, format_]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    # Parsear BBOX
    try:
        minx, miny, maxx, maxy = map(float, bbox.split(','))
    except ValueError:
        return Response("BBOX inválido. Debe estar en el formato minx,miny,maxx,maxy.", status=400)

    # Cargar imagen base
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'
    try:
        img_response = requests.get(img_url, timeout=10)
        img_response.raise_for_status()
        img = Image.open(BytesIO(img_response.content))
    except Exception as e:
        return Response(f"Error al cargar la imagen base: {str(e)}", status=500)

    # Calcular área de recorte en píxeles
    scale_x = PIXELS_PER_UNIT * (maxx - minx) / (ORIGIN_X - (ORIGIN_X + IMAGE_WIDTH * PIXELS_PER_UNIT))
    scale_y = PIXELS_PER_UNIT * (maxy - miny) / (ORIGIN_Y - (ORIGIN_Y + IMAGE_HEIGHT * PIXELS_PER_UNIT))

    crop_x1 = int((minx - ORIGIN_X) / scale_x)
    crop_y1 = int((ORIGIN_Y - maxy) / scale_y)
    crop_x2 = int((maxx - ORIGIN_X) / scale_x)
    crop_y2 = int((ORIGIN_Y - miny) / scale_y)

    # Recortar y escalar la imagen
    img_cropped = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    img_resized = img_cropped.resize((width, height), Image.Resampling.LANCZOS)

    # Generar la respuesta
    img_io = BytesIO()
    img_resized.save(img_io, 'PNG')
    img_io.seek(0)
    return Response(img_io.getvalue(), content_type='image/png')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)













