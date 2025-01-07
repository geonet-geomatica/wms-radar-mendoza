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
    width = int(request.args.get('WIDTH', 256))  # Dimensiones por defecto
    height = int(request.args.get('HEIGHT', 256))
    crs = request.args.get('CRS', 'EPSG:4326')
    format_ = request.args.get('FORMAT', 'image/png')

    # Validar parámetros
    if not bbox or not all([width, height, crs, format_]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    # Convertir BBOX en coordenadas
    try:
        minx, miny, maxx, maxy = map(float, bbox.split(','))
    except ValueError:
        return Response("BBOX no tiene el formato correcto. Debe ser minx,miny,maxx,maxy.", status=400)

    # URL de la imagen del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperar la imagen de radar
        img_response = requests.get(img_url)
        img_response.raise_for_status()  # Verificar si hubo errores en la solicitud

        # Abrir la imagen del radar
        img = Image.open(BytesIO(img_response.content))

        # Dimensiones reales del radar (BoundingBox total del radar)
        radar_bbox = (-71.7249353229, -37.4356023471, -64.9942298547, -31.2320003192)
        radar_width, radar_height = img.size

        # Calcular la escala entre BBOX solicitado y el BBOX real del radar
        scale_x = radar_width / (radar_bbox[2] - radar_bbox[0])
        scale_y = radar_height / (radar_bbox[3] - radar_bbox[1])

        # Calcular la región de la imagen que corresponde al BBOX solicitado
        crop_left = int((minx - radar_bbox[0]) * scale_x)
        crop_upper = int((radar_bbox[3] - maxy) * scale_y)
        crop_right = int((maxx - radar_bbox[0]) * scale_x)
        crop_lower = int((radar_bbox[3] - miny) * scale_y)

        # Recortar y escalar la imagen según los parámetros solicitados
        cropped_img = img.crop((crop_left, crop_upper, crop_right, crop_lower))
        resized_img = cropped_img.resize((width, height), Image.ANTIALIAS)

        # Convertir la imagen a PNG
        img_io = BytesIO()
        resized_img.save(img_io, 'PNG')
        img_io.seek(0)

        # Crear la respuesta con la imagen solicitada
        response = Response(img_io.getvalue(), content_type='image/png')
        response.headers['Content-Disposition'] = 'inline; filename="radar.png"'

        return response
    except Exception as e:
        return Response(f"Error al obtener la imagen: {str(e)}", status=500)

if __name__ == "__main__":
    # Utilizamos el puerto de la variable de entorno o el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)







