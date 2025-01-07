from flask import Flask, Response, request
from io import BytesIO
from PIL import Image
import requests
import os

app = Flask(__name__)

# Coordenadas de los límites del mapa
BOUNDING_BOX = {
    "minx": -71.7249353229,
    "miny": -37.4356023471,
    "maxx": -64.9942298547,
    "maxy": -31.2320003192
}

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
    capabilities = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <WMS_Capabilities xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"1.3.0\">
        <Service>
            <Name>WMS</Name>
            <Title>Radar Mendoza</Title>
            <Abstract>Servicio WMS para mostrar radar de Mendoza</Abstract>
            <KeywordList>
                <Keyword>Radar</Keyword>
                <Keyword>Mendoza</Keyword>
            </KeywordList>
            <OnlineResource xlink:type=\"simple\" xlink:href=\"https://wms-radar-mendoza.onrender.com/wms\" />
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
                                <OnlineResource xlink:type=\"simple\" xlink:href=\"https://wms-radar-mendoza.onrender.com/wms\" />
                            </Get>
                        </HTTP>
                    </DCPType>
                </GetMap>
            </Request>
            <Layer>
                <Title>Radar Mendoza</Title>
                <Abstract>Datos de radar de la provincia de Mendoza</Abstract>
                <CRS>EPSG:4326</CRS>
                <BoundingBox CRS=\"EPSG:4326\" minx=\"{BOUNDING_BOX['minx']}\" miny=\"{BOUNDING_BOX['miny']}\" maxx=\"{BOUNDING_BOX['maxx']}\" maxy=\"{BOUNDING_BOX['maxy']}\" />
                <Layer queryable=\"1\">
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

    # Validar BBOX contra los límites definidos
    try:
        bbox_values = list(map(float, bbox.split(',')))
        if not (
            BOUNDING_BOX['minx'] <= bbox_values[0] <= BOUNDING_BOX['maxx'] and
            BOUNDING_BOX['miny'] <= bbox_values[1] <= BOUNDING_BOX['maxy'] and
            BOUNDING_BOX['minx'] <= bbox_values[2] <= BOUNDING_BOX['maxx'] and
            BOUNDING_BOX['miny'] <= bbox_values[3] <= BOUNDING_BOX['maxy']
        ):
            return Response("BBOX fuera de los límites permitidos.", status=400)
    except ValueError:
        return Response("Formato de BBOX no válido.", status=400)

    # URL de la imagen del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperar la imagen de radar
        img_response = requests.get(img_url)
        img_response.raise_for_status()  # Verificar si hubo errores en la solicitud

        img = Image.open(BytesIO(img_response.content))

        # Convertir la imagen a PNG
        img_io = BytesIO()
        img.save(img_io, 'PNG')
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





