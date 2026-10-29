# Casandra – Predictor de tasas de evacuación (Oráculo)

Microservicio que estima cuántas personas saldrán de un edificio en los próximos 10 segundos,
a partir del estado de su evacuación y de sus características estructurales. Está pensado para
ser consultado en tiempo de ejecución por un simulador de evacuación exterior (DEMPS), que
incorpora así a los evacuados de cada edificio de forma dinámica.

El modelo es una red neuronal densa (64–32–16, ReLU) entrenada con datos del simulador de
evacuación en interiores AB-BES (NetLogo 3D).

Imagen publicada: [`ssstefany/casandra:version02`](https://hub.docker.com/r/ssstefany/casandra)

## Estructura

```
broker.py                    Programa principal: modo train | predict
casandra_libs/
  casandra.py                Servicio web (GET y POST en /predict, puerto 10800)
  oraculo.py                 Carga el modelo y el escalador y genera predicciones
  training.py                Entrenamiento de la red neuronal
  training_data/             Archivos CSV de AB-BES (no incluidos en el repositorio)
  training_model/            Modelo entrenado (model.keras) y escalador (scaler.pkl)
Dockerfile
training.yml                 Docker Compose para entrenar
predict.yml                  Docker Compose para levantar el servicio
```

## Uso rápido

```bash
docker run -d --name oraculo -p 10800:10800 ssstefany/casandra:version02 predict
```

El servicio queda disponible en `http://localhost:10800`.

## Consulta

Se envía un objeto JSON con la clave `cases`: una lista con un vector de 13 valores por edificio.
La respuesta es una lista con la tasa estimada (personas por intervalo de 10 s) para cada edificio,
en el mismo orden.

**POST**

```bash
curl -X POST http://localhost:10800/predict \
     -H "Content-Type: application/json" \
     -d '{"cases":[[465,120,60,35,345,15,0,1,3,3,3,50,0.9],[400,90,60,53,310,4,0,2,7,6,4,70,0.9]]}'
```

**GET**

```
http://localhost:10800/predict?data={"cases":[[465,120,60,35,345,15,0,1,3,3,3,50,0.9]]}
```

Respuesta: `[6.00, 11.62]`

### Vector de entrada (en este orden)

| # | Valor |
|---|---|
| 1 | Total de ocupantes |
| 2 | Evacuados acumulados |
| 3 | Tiempo de respuesta (s) |
| 4 | Personas en la zona de salida (agentes a ≤ 4,8 m de la salida, del lado de la calle) |
| 5 | Personas aún en el interior |
| 6 | Número de pisos |
| 7 | Ocupantes en pánico al inicio |
| 8 | Número de escaleras |
| 9 | Ancho de salida (celdas de 0,4 m) |
| 10 | Ancho de pasillos (celdas de 0,4 m) |
| 11 | Ancho de escaleras (celdas de 0,4 m) |
| 12 | Ancho del edificio (celdas de 0,4 m) |
| 13 | Umbral de pánico λ |

Si un vector no tiene 13 valores, el servicio responde con una lista vacía.

## Entrenamiento

1. Copiar los archivos CSV de AB-BES (separador `;`) en `casandra_libs/training_data/`.
2. Ejecutar:

   ```bash
   docker compose -f training.yml up
   ```

3. El modelo y el escalador se guardan en `casandra_libs/training_model/`. Al finalizar se
   imprimen las métricas sobre el conjunto de prueba (MAE, MSE y R²).

El entrenamiento divide los datos en 80 % / 20 % **por corrida** (no por registro), estratificado
por combinación de parámetros, y usa como variable objetivo el número de personas que salen del
edificio en el intervalo de 10 s **siguiente**.

## Construir la imagen

Con el modelo entrenado en `casandra_libs/training_model/`:

```bash
docker build -t ssstefany/casandra:version02 .
docker compose -f predict.yml up
```

## Versiones

- **version02**: modelo reentrenado con 22 320 corridas de AB-BES (MAE 1,66; MSE 4,50; R² 0,59
  sobre 4 464 corridas de prueba); división por corrida; predicción del intervalo siguiente;
  lectura de archivos CSV; modelo incluido en la imagen.
- **version01**: versión original.

## Referencia

A. S. Balboa Carvajal, G. Astudillo Muñoz y R. Noel, "A Container-Based Software Architecture for
Coupling Heterogeneous Agent-Based Evacuation Models using Machine Learning", *XXIX Congresso
Ibero-Americano em Engenharia de Software (CIbSE 2026)*, 2026.
