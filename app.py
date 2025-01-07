from flask import Flask, Response
from owslib.wms import WebMapService
import requests
from io import BytesIO
from PIL import Image
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bienvenido al servicio WMS de Radar Mendoza"

@app.route('/wms')
def wms():
    # URL de la imagen del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperamos la imagen de radar
        img_response = requests.get(img_url)
        img_response.raise_for_status()  # Verificar si hubo errores en la solicitud

        img = Image.open(BytesIO(img_response.content))

        # Convertir la imagen a PNG
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        # Crear la respuesta WMS para la imagen
        response = Response(img_io.getvalue(), content_type='image/png')
        response.headers['Content-Disposition'] = 'inline; filename="radar.png"'

        return response
    except Exception as e:
        return Response(f"Error al obtener la imagen: {str(e)}", status=500)

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

if __name__ == "__main__":
    # Utilizamos el puerto de la variable de entorno o el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


