from flask import Flask, Response
from owslib.wms import WebMapService
import requests
from io import BytesIO
from PIL import Image
import io

app = Flask(__name__)

@app.route('/')
def index():
    return "Bienvenido al servicio WMS de Radar Mendoza"

@app.route('/wms')
def wms():
    service = WebMapService('https://www2.contingencias.mendoza.gov.ar/radar/google.png')
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    # Recuperamos la imagen de radar
    img_response = requests.get(img_url)
    img = Image.open(BytesIO(img_response.content))

    # Establecer el tipo de contenido de la imagen
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # Definir los límites en coordenadas geográficas (EPSG:4326)
    sw = [-37.4356023471, -71.7249353229]  # Lower Left: LAT, LON
    ne = [-31.2320003192, -64.9942298547]  # Upper Right: LAT, LON

    # Crear la respuesta WMS para la imagen
    response = Response(img_io.getvalue(), content_type='image/png')
    response.headers['Content-Disposition'] = 'inline; filename="radar.png"'

    return response

@app.route('/wms/capabilities')
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
                <CRS>EPSG:4326</CRS> <!-- Definir la proyección correcta -->
                <BoundingBox CRS="EPSG:4326" minx="-71.7249353229" miny="-37.4356023471" maxx="-64.9942298547" maxy="-31.2320003192" />
                <Layer queryable="1">
                    <Name>radar</Name>
                    <Title>Radar Mendoza</Title>
                </Layer>
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

if __name__ == '__main__':
    app.run(debug=True)

