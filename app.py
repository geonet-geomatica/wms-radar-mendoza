from flask import Flask, request, Response
from owslib.wms import WebMapService  # Corregir la importación aquí

app = Flask(__name__)

@app.route('/wms', methods=['GET'])
def wms_service():
    service = request.args.get('SERVICE')
    request_type = request.args.get('REQUEST')
    
    if service == 'WMS':
        if request_type == 'GetCapabilities':
            return get_capabilities()
        elif request_type == 'GetMap':
            return get_map()
        else:
            return "Unknown request type", 400
    return "Invalid WMS service", 400

def get_capabilities():
    # Aquí puedes definir los parámetros de tu servicio WMS
    capabilities = """<?xml version="1.0" encoding="UTF-8"?>
    <WMS_Capabilities version="1.3.0">
        <Service>
            <Name>WMS</Name>
            <Title>Radar Mendoza</Title>
            <Abstract>Servicio WMS para mostrar radar de Mendoza</Abstract>
            <KeywordList>
                <Keyword>Radar</Keyword>
                <Keyword>Mendoza</Keyword>
            </KeywordList>
            <OnlineResource xlink:type="simple" xlink:href="https://<nombre-de-tu-app>.onrender.com/wms" />
        </Service>
        <Capability>
            <Request>
                <GetCapabilities>
                    <Format>application/xml</Format>
                </GetCapabilities>
                <GetMap>
                    <Format>image/png</Format>
                    <Layer queryable="1">
                        <Name>radar</Name>
                    </Layer>
                </GetMap>
            </Request>
        </Capability>
    </WMS_Capabilities>"""
    return Response(capabilities, mimetype="application/xml")

def get_map():
    # Aquí iría el código para generar la imagen solicitada en la capa WMS
    # Por ejemplo, podrías servir una imagen PNG.
    image_url = "https://www2.contingencias.mendoza.gov.ar/radar/muestraimagen.php?imagen=google.png&sw=-37.40959444444444,-71.71962222222223&ne=-31.22909166666667,-65.02164166666667&centro=-34.0,-68.4&zoom=7"
    img_response = requests.get(image_url)
    return Response(img_response.content, mimetype="image/png")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

