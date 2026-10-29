import os
import tensorflow as tf
import numpy as np
import tensorflow as tf
import joblib

class ModelFileException(Exception):
    pass

class Oraculo:
    def __init__(self, model_file, scaler_file):
        
        # Si los archivos del modelo entrenado no existen, se
        # generan excepciones del tipo ModelFileException
        if not os.path.exists(model_file):
            raise ModelFileException(f"El archivo {model_file} no existe.")
        if not os.path.exists(scaler_file):
            raise ModelFileException(f"El archivo {scaler_file} no existe")
        
        # A partir de los archivos keras y pkl se construye
        # el modelo entrenado
        self.model = tf.keras.models.load_model(model_file)
        self.scaler = joblib.load(scaler_file)
        
    def execute(self, input_data):
        predictions = []
        try:
            cases = input_data['cases']
            for case in cases:
                x = np.array(case).reshape(1, -1)
                x_scaled = self.scaler.transform(x)  # Escalar los datos
                prediction = self.model.predict(x_scaled)  # Hacer la predicción
                predictions.append(float(prediction[0][0]))  # Almacenar la predicción

        except KeyError:
            print("El formato JSON no contiene 'cases'")
        except Exception as e:
            print(f"Error al procesar los datos: {e}")
        
        return predictions
