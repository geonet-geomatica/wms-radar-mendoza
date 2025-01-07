from flask import Flask, Response, request, jsonify
import requests

app = Flask(__name__)

# URL base para obtener la imagen del radar
RADAR_IMAGE_URL = "https://www2.contingencias.mendoza.gov.ar/radar/muestraimagen.php"
RADAR_IMAGE_PARAMS = {
    "imagen": "google.png",
    "sw": "-37.40959444444444,-71.71962222222223",
    "ne": "-31.22909166666667,-65.02164166666667",
    "centro": "-34.0,-68.4",
    "zoom": "7"
}

@app.route("/wms", methods=["GET"])
def wms():
    service = request.args.get("SERVICE", "").upper()
    request_type = request.args.get("REQUEST", "").upper()

    if service != "WMS":
        return Response("Invalid SERVICE parameter", status=400)

    if request_type == "GETCAPABILITIES":
        return get_capabilities()
    elif request_type == "GETMAP":
        return get_map()
    else:
        return Response("Invalid REQUEST parameter", status=400)

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
                <BoundingBox CRS="EPSG:4326" minx="-71.71962222222223" miny="-37.40959444444444" maxx="-65.02164166666667" maxy="-31.22909166666667" />
                <Layer queryable="1">
                    <Name>radar</Name>
                    <Title>Radar Mendoza</Title>
                </Layer>
            </Layer>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    # Descargar la imagen del radar desde la URL remota
    response = requests.get(RADAR_IMAGE_URL, params=RADAR_IMAGE_PARAMS, stream=True)

    if response.status_code == 200:
        return Response(response.content, mimetype="image/png")
    else:
        return Response("Error fetching radar image", status=500)

@app.route("/")
def home():
    return jsonify({"message": "Servicio WMS para el radar de Mendoza está funcionando."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
