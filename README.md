# Riesgo de cancelación de reservas hoteleras

Aplicación web que estima la probabilidad de que una reserva hotelera sea cancelada, a partir de sus características.
Es la fase de despliegue (Fase 6) de un proyecto de analítica de datos desarrollado con la metodología CRISP-DM.

- **Modelo:** XGBoost (incluye la preparación de los datos).
- **Datos:** Hotel Booking Demand (Antonio, Almeida y Nunes, 2019), reservas de dos hoteles en Portugal entre 2015 y 2017.
- **Desempeño en datos de prueba:** AUC-ROC 0,899 · Recall 0,784 · Precision 0,646 · F1 0,708.

## Archivos

| Archivo | Contenido |
|---|---|
| `app.py` | Aplicación en Streamlit |
| `modelo_cancelacion.pkl` | Modelo entrenado, exportado desde Google Colab |
| `configuracion_modelo.json` | Variables, opciones y rangos que usa la aplicación |
| `requirements.txt` | Librerías necesarias, con las mismas versiones usadas para entrenar el modelo |

## Autores

Juan Felipe Martínez Ortega · Juan José Ariza Quintero
