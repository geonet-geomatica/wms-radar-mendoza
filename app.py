from flask import Flask, Response, request
from io import BytesIO
from PIL import Image
import requests
import os
import pyproj

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
                <CRS>EPSG:3857</CRS>
                <BoundingBox CRS="EPSG:3857" minx="-7598394" miny="-4020959" maxx="-7542000" maxy="-3955000" />
                <Layer queryable="1">
                    <Name>radar</Name>
                    <Title>Radar Mendoza</Title>
                </Layer>
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

    # Parsear el BBOX y transformarlo de EPSG:3857 a EPSG:4326
    try:
        bbox_vals = list(map(float, bbox.split(',')))
        transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
        minx, miny = transformer.transform(bbox_vals[0], bbox_vals[1])
        maxx, maxy = transformer.transform(bbox_vals[2], bbox_vals[3])
    except Exception as e:
        return Response(f"Error al transformar coordenadas del BBOX: {str(e)}", status=400)

    # URL de la imagen original del radar
    img_url = 'https://www2.contingencias.mendoza.gov.ar/radar/google.png'

    try:
        # Recuperar la imagen original
        img_response = requests.get(img_url, timeout=10)
        img_response.raise_for_status()
        img = Image.open(BytesIO(img_response.content))

        # Recortar y redimensionar la imagen para que coincida con el BBOX solicitado
        img_width, img_height = img.size

        origin_x, origin_y = -68.25, -34.24966653449996  # Coordenadas de origen de la imagen
        img_bbox = (-68.25, -34.24966653449996, -67.75032747733738, -33.74999999999999)
        
        scale_x = img_width / (img_bbox[2] - img_bbox[0])
        scale_y = img_height / (img_bbox[3] - img_bbox[1])

        crop_box = (
            int((minx - img_bbox[0]) * scale_x),
            int((img_bbox[3] - maxy) * scale_y),
            int((maxx - img_bbox[0]) * scale_x),
            int((img_bbox[3] - miny) * scale_y),
        )

        cropped_img = img.crop(crop_box)
        resized_img = cropped_img.resize((width, height), Image.Resampling.LANCZOS)

        # Guardar la imagen como PNG
        img_io = BytesIO()
        resized_img.save(img_io, 'PNG')
        img_io.seek(0)

        return Response(img_io.getvalue(), content_type='image/png')

    except Exception as e:
        return Response(f"Error al procesar la solicitud GetMap: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)












