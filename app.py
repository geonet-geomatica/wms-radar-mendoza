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
                    <DCPType>
                        <HTTP>
                            <Get>
                                <OnlineResource xlink:type="simple" xlink:href="https://wms-radar-mendoza.onrender.com/wms?SERVICE=WMS&amp;REQUEST=GetCapabilities" />
                            </Get>
                        </HTTP>
                    </DCPType>
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
                <CRS>EPSG:3857</CRS>
                <BoundingBox CRS="EPSG:3857" minx="-7984383.277325993" miny="-4499999.319269053" maxx="-7235124.571920742" maxy="-3662915.595787793" />
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    bbox = request.args.get('BBOX')
    width = int(request.args.get('WIDTH', 256))
    height = int(request.args.get('HEIGHT', 256))
    crs = request.args.get('CRS', 'EPSG:3857')
    format_ = request.args.get('FORMAT', 'image/png')

    if not all([bbox, width, height, crs, format_]):
        return Response("Faltan parámetros obligatorios para GetMap (BBOX, WIDTH, HEIGHT, CRS, FORMAT).", status=400)

    if format_.lower() != 'image/png':
        return Response("Formato no soportado. Solo se soporta image/png.", status=400)

    # URL de la imagen del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperar la imagen original
        img_response = requests.get(img_url, timeout=10)
        img_response.raise_for_status()

        img = Image.open(BytesIO(img_response.content))

        # Redimensionar la imagen
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

        # Convertir a fondo transparente si es necesario
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        img_io = BytesIO()
        img_resized.save(img_io, 'PNG')
        img_io.seek(0)

        return Response(img_io.getvalue(), content_type='image/png')

    except Exception as e:
        return Response(f"Error al procesar la solicitud GetMap: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
















