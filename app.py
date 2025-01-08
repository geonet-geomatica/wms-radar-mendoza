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
    request_type = request.args.get('REQUEST', '').upper()

    if request_type == 'GETCAPABILITIES':
        return get_capabilities()
    elif request_type == 'GETMAP':
        return get_map()
    else:
        return Response("Solicitud no válida. Especifique un parámetro REQUEST válido (GetCapabilities o GetMap).", status=400)

def get_capabilities():
    capabilities = """<?xml version="1.0" encoding="UTF-8"?>
    <WMS_Capabilities xmlns="http://www.opengis.net/wms" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.3.0">
        <Service>
            <Name>WMS</Name>
            <Title>Radar Mendoza</Title>
            <Abstract>Servicio WMS para mostrar radar de Mendoza</Abstract>
            <KeywordList>
                <Keyword>Radar</Keyword>
                <Keyword>Mendoza</Keyword>
            </KeywordList>
            <OnlineResource xlink:type="simple" xlink:href="https://wms-radar-mendoza.onrender.com/wms?SERVICE=WMS&amp;REQUEST=GetCapabilities" />
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
                                <OnlineResource xlink:type="simple" xlink:href="https://wms-radar-mendoza.onrender.com/wms?SERVICE=WMS&amp;REQUEST=GetMap" />
                            </Get>
                        </HTTP>
                    </DCPType>
                </GetMap>
            </Request>
            <Layer>
                <Name>radar</Name>
                <Title>Radar Mendoza</Title>
                <Abstract>Datos de radar de la provincia de Mendoza</Abstract>
                <CRS>EPSG:4326</CRS>
                <BoundingBox CRS="EPSG:4326" minx="-71.71962222222223" miny="-37.40959444444444" maxx="-65.02164166666667" maxy="-31.22909166666667" />
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    bbox = request.args.get('BBOX')
    width = int(request.args.get('WIDTH', 256))
    height = int(request.args.get('HEIGHT', 256))
    crs = request.args.get('CRS', 'EPSG:4326')
    format_ = request.args.get('FORMAT', 'image/png')

    if not all([bbox, width, height, crs, format_]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    # Parsear coordenadas BBOX
    bbox_coords = list(map(float, bbox.split(',')))
    minx, miny, maxx, maxy = bbox_coords

    # URL de la imagen base
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Descargar la imagen base
        img_response = requests.get(img_url, timeout=10)
        img_response.raise_for_status()

        img = Image.open(BytesIO(img_response.content))

        # Transformar la imagen para ajustarse al BBOX
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height

        # Escalar la imagen al tamaño solicitado
        scaled_width = width
        scaled_height = int(width / aspect_ratio)

        if scaled_height < height:
            scaled_height = height
            scaled_width = int(height * aspect_ratio)

        img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # Recortar la imagen para que coincida con el BBOX
        crop_x1 = int((minx + 180) / 360 * scaled_width)
        crop_x2 = int((maxx + 180) / 360 * scaled_width)
        crop_y1 = int((90 - maxy) / 180 * scaled_height)
        crop_y2 = int((90 - miny) / 180 * scaled_height)

        img_cropped = img_resized.crop((crop_x1, crop_y1, crop_x2, crop_y2))

        # Convertir a formato PNG
        img_io = BytesIO()
        img_cropped.save(img_io, 'PNG')
        img_io.seek(0)

        return Response(img_io.getvalue(), content_type='image/png')

    except Exception as e:
        return Response(f"Error al procesar la solicitud GetMap: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

















