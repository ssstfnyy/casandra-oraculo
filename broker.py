#!/usr/bin/env python3

import signal
import os
import sys
from http.server import HTTPServer

from casandra_libs.casandra import Casandra
from casandra_libs.oraculo import Oraculo
from casandra_libs.oraculo import ModelFileException
from casandra_libs.training import NeuralNetwork

BASE_DIR        =  os.path.dirname(os.path.abspath(__file__))
KERAS_FILE      = BASE_DIR + "/casandra_libs/training_model/model.keras"
PKL_FILE        = BASE_DIR + "/casandra_libs/training_model/scaler.pkl"
TRAIN_DATA_PATH = BASE_DIR + "/casandra_libs/training_data"
          

def runCasandra(model_file: str, scaler_file: str, port=10800):

    # Agregar a la clase Casandra el objeto Oraculo
    try:
        Casandra.oraculo = Oraculo(model_file, scaler_file)  
    except ModelFileException as e:
        print(f"{e}")
    else:
        serverAddress = ('', port)
        casandraServer = HTTPServer(server_address=serverAddress, RequestHandlerClass=Casandra)
        
        print(f'Servidor Casandra ejecutándose en http://localhost:{port}')
        sys.stdout.flush()
        casandraServer.serve_forever()
    
    
# Se debe capturar la señal ctrl+C para permitir
# que el contenedor se apague correctamente
def signal_handler(sig, frame):
    print("Finalizando Casandra...")
    sys.exit(0)

def uso():
    print("Use: "+ sys.argv[0] + " train | predict")
    sys.stdout.flush() 
    sys.exit()

def training():
    print("Entrenamiento...")
    neural_network = NeuralNetwork(data_path = TRAIN_DATA_PATH, model_file=KERAS_FILE, scaler_file=PKL_FILE)
    neural_network.execute()
    sys.stdout.flush() 
    
def predict():
    runCasandra(model_file=KERAS_FILE, scaler_file=PKL_FILE)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    for i in range(1, len(sys.argv)):
        #print(sys.argv[i], end = " ")
    
        if sys.argv[i] == "predict":
            predict()
        elif sys.argv[i] == "train":
            training()
            
            
if __name__ == "__main__":
    main()

    