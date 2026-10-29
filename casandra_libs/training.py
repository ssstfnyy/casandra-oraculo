import glob
import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm import tqdm

class NeuralNetwork:
    def __init__(self, data_path, model_file, scaler_file):
        self.data_path   = data_path 
        self.model_file  = model_file
        self.scaler_file = scaler_file
        # CAMBIO: acepta .xlsx (formato anterior) y .csv con separador ';' (salida de AB-BES)
        self.excel_files = sorted(glob.glob(self.data_path + "/*.xlsx") + glob.glob(self.data_path + "/*.csv"))
        self.df = pd.DataFrame


    def __read_excel(self):
        df_list = []   

        for file in tqdm(self.excel_files, desc="Processing data files", unit="file"):
            if file.endswith(".csv"):
                df = pd.read_csv(file, sep=';')
            else:
                df = pd.read_excel(file)
            df = df.sort_values(by=['RunNumber', 'Step'])
            # CAMBIO: identificador único de corrida (RunNumber se repite entre archivos)
            df['CorridaID'] = os.path.basename(file) + "-" + df['RunNumber'].astype(str)
            # CAMBIO: tasa de evacuación del PRÓXIMO intervalo de 10 s (t -> t+10),
            # que es lo que DEMPS necesita predecir. Antes se usaba diff(1), que
            # corresponde al intervalo anterior (t-10 -> t).
            df['tasaEvacuados'] = (df['nInterior'] - df.groupby('RunNumber')['nInterior'].shift(-1)).fillna(0).abs()
            df_list.append(df)

        self.df = pd.concat(df_list, ignore_index=True)

    def __data_preprocessing(self):
        # Seleccionar las características (x)
        self.features = ['TotalPeatones',
                    'TotalEvacuados',
                    'TiempoDeRespuesta',
                    'nExterior',
                    'nInterior',
                    'NumeroDePisos',
                    'NumeroDeInfectados',
                    'NumeroDeEscaleras',
                    'AnchoDeSalida',
                    'AnchoDePasillos',
                    'AnchoDeEscaleras',
                    'AnchoDeEdificio',
                    'Lambda']
                    #'Step'
        # Seleccionar variable objetivo (y)
        target = 'tasaEvacuados'

        # CAMBIO: división 80/20 por corrida y estratificada por combinación de
        # parámetros, para que los registros de una misma corrida no queden
        # repartidos entre entrenamiento y prueba.
        params = [c for c in self.df.columns if c not in
                  ('RunNumber', 'Step', 'nExterior', 'nInterior', 'TotalEvacuados', 'tasaEvacuados', 'CorridaID')]
        corridas = self.df[params + ['CorridaID']].drop_duplicates('CorridaID')
        rng = np.random.RandomState(42)
        test_ids = []
        for _, grupo in corridas.groupby(params):
            ids = grupo['CorridaID'].values
            n_test = max(1, int(round(0.2 * len(ids))))
            test_ids.extend(rng.choice(ids, n_test, replace=False))
        es_test = self.df['CorridaID'].isin(set(test_ids))

        X_train, X_test = self.df.loc[~es_test, self.features], self.df.loc[es_test, self.features]
        self.y_train, self.y_test = self.df.loc[~es_test, target], self.df.loc[es_test, target]
        print(f"Corridas: {corridas.shape[0]} | entrenamiento: {corridas.shape[0] - len(test_ids)} | prueba: {len(test_ids)}")

        # Escalar los datos para normalización
        scaler = StandardScaler()
        self.X_train_scaled = scaler.fit_transform(X_train.values)
        self.X_test_scaled = scaler.transform(X_test.values)

        # Guardar el escalador
        os.makedirs(os.path.dirname(self.scaler_file), exist_ok=True)  # CAMBIO: crea la carpeta si no existe
        joblib.dump(scaler, self.scaler_file)  


    def __create_and_trainning_model(self):         
        # Definir el modelo
        model = Sequential()

        # Añadir capas al modelo
        model.add(Dense(64, input_dim=len(self.features), activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(16, activation='relu'))

        # Capa de salida (1 sola neurona para regresión)
        model.add(Dense(1, activation='linear'))

        # Compilar el modelo
        model.compile(optimizer='adam', loss='mean_absolute_error')
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        # Entrenar el modelo
        model.fit(self.X_train_scaled, self.y_train, epochs=50, batch_size=32, validation_split=0.2, callbacks=[early_stopping])

        # CAMBIO: métricas sobre el conjunto de prueba, para reportar en la tesis
        y_pred = model.predict(self.X_test_scaled).ravel()
        print(f"Prueba -> MAE: {mean_absolute_error(self.y_test, y_pred):.4f} | "
              f"MSE: {mean_squared_error(self.y_test, y_pred):.4f} | "
              f"R2: {r2_score(self.y_test, y_pred):.4f}")

        # Guardar el modelo
        model.save(self.model_file)

    def execute(self):
        if len(self.excel_files) > 0 :
            self.__read_excel()
            self.__data_preprocessing()
            self.__create_and_trainning_model()
        else:
            print(f"La ruta {self.data_path} no contiene archivos de entrenamiento (.xlsx o .csv).")
