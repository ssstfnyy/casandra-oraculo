#!/usr/bin/env python3


from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import json


# maneja las peticiones HTTP
#
# Llamada via GET
#   http://localhost:8080/predict?data={"cases":[[600,577,30,138,23,15,15,1,6,5,4,50,0.9],[600,577,30,138,23,15,15,1,6,5,4,50,0.8]]}

class Casandra(BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, content_type='application/json'):
            # Código de estado de la respuesta (por defecto 200, que significa éxito).
            # Tipo de contenido que será enviado en la respuesta (por defecto JSON).
            self.send_response(status_code) 
            self.send_header('Content-type', content_type) 
            self.end_headers() 

    def _predict(self, data_to_predict):
        try:
            input_data = json.loads(data_to_predict)                
            predictions = self.oraculo.execute(input_data)  # Ejecutar las predicciones con el oráculo existente

            self._set_response()
            self.wfile.write(json.dumps(predictions).encode('utf-8'))  # Retornar predicciones en formato JSON
        except json.JSONDecodeError:
            self.send_error(400, "Error en el formato del JSON")
        
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        
        if parsed_path.path == '/predict':
            #print(f"{query=}")
            
            if 'data' in query:
                values = query['data'][0]
                # En values está el json
                # {"cases":[ features caso 1 ], ..., [features caso i], ... , [features caso N]
                self._predict(values)
                '''
                ### Eliminar este código. Se trasladó al método _predict()
                try:
                    input_data = json.loads(values)                
                    predictions = self.oraculo.execute(input_data)  # Ejecutar las predicciones con el oráculo existente

                    self._set_response()
                    self.wfile.write(json.dumps(predictions).encode('utf-8'))  # Retornar predicciones en formato JSON
                except json.JSONDecodeError:
                    self.send_error(400, "Error en el formato del JSON")
                '''
                
        else:
            self.send_error(404, "Recurso no encontrado")
        
            
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/predict':
            # se le debe consultar a la máquina y
            # lo que devuelva, retornarlo
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            self._predict(post_data)
            '''
            ### Eliminar este código. Se trasladó al método _predict()
            try:
                input_data = json.loads(post_data)              # Leer el archivo JSON del cuerpo de la solicitud
                predictions = self.oraculo.execute(input_data)  # Ejecutar las predicciones con el oráculo existente

                self._set_response()
                self.wfile.write(json.dumps(predictions).encode('utf-8'))  # Retornar predicciones en formato JSON
            except json.JSONDecodeError:
                self.send_error(400, "Error en el formato del JSON")
            '''
        else:
            self.send_error(404, "Recurso no encontrado")


            

    