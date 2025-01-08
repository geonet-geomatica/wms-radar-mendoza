from flask import Flask, Response, request
from io import BytesIO
from PIL import Image, ImageOps
import requests
import os

app = Flask(__name__)

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
                <CRS>EPSG:4326</CRS>
                <BoundingBox CRS="EPSG:4326" minx="-37.4356023471" miny="-71.7249353229" maxx="-31.2320003192" maxy="-64.9942298547" />
                <Layer queryable="1">
                    <Name>radar</Name>
                    <Title>Radar Mendoza</Title>
                </Layer>
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    # Obtener parámetros de la solicitud
    bbox = request.args.get('BBOX')
    width = request.args.get('WIDTH')
    height = request.args.get('HEIGHT')
    crs = request.args.get('CRS')
    format_ = request.args.get('FORMAT')
    layers = request.args.get('LAYERS')

    # Validar parámetros obligatorios
    if not all([bbox, width, height, crs, format_, layers]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT, LAYERS).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    # Procesar BBOX
    try:
        bbox = list(map(float, bbox.split(',')))
        if len(bbox) != 4:
            raise ValueError("BBOX debe tener 4 valores: miny, minx, maxy, maxx (EPSG:4326).")
    except Exception:
        return Response("BBOX inválido. Debe ser un string con 4 valores separados por comas.", status=400)

    # Procesar tamaño de imagen
    try:
        width = int(width)
        height = int(height)
    except ValueError:
        return Response("WIDTH y HEIGHT deben ser números enteros.", status=400)

    # URL de la imagen del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperar la imagen original
        img_response = requests.get(img_url, timeout=10)
        img_response.raise_for_status()

        img = Image.open(BytesIO(img_response.content))

        # Transformar la imagen base al BBOX solicitado
        img_width, img_height = img.size
        original_bbox = [-71.7249353229, -37.4356023471, -64.9942298547, -31.2320003192]  # BBOX original de la imagen base
        scale_x = img_width / (original_bbox[2] - original_bbox[0])
        scale_y = img_height / (original_bbox[3] - original_bbox[1])

        # Calcular los píxeles de recorte en base al BBOX solicitado
        minx, miny, maxx, maxy = bbox
        left = int((minx - original_bbox[0]) * scale_x)
        upper = int((miny - original_bbox[1]) * scale_y)
        right = int((maxx - original_bbox[0]) * scale_x)
        lower = int((maxy - original_bbox[1]) * scale_y)

        # Recortar la imagen
        img_cropped = img.crop((left, upper, right, lower))

        # Redimensionar a las dimensiones solicitadas
        img_resized = img_cropped.resize((width, height), Image.Resampling.LANCZOS)

        # Convertir a PNG
        img_io = BytesIO()
        img_resized.save(img_io, 'PNG')
        img_io.seek(0)

        return Response(img_io.getvalue(), content_type='image/png')

    except Exception as e:
        return Response(f"Error al procesar la solicitud GetMap: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)










