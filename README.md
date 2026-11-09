# Riesgo de cancelación de reservas hoteleras

Aplicación web que estima la probabilidad de que una reserva hotelera sea cancelada, a partir de sus características.
Es la fase de despliegue (Fase 6) de un proyecto de analítica de datos desarrollado con la metodología CRISP-DM.

- **Modelo:** XGBoost (incluye la preparación de los datos).
- **Datos:** Hotel Booking Demand (Antonio, Almeida y Nunes, 2019), reservas de dos hoteles en Portugal entre 2015 y 2017.
- **Desempeño en datos de prueba:** AUC-ROC 0,899 · Recall 0,784 · Precision 0,646 · F1 0,708.

## Funciones de la aplicación

- **Evaluar una reserva:** formulario organizado en tres pasos (datos de la reserva, huéspedes y solicitudes, canal de venta y cliente). Al presionar *Calcular riesgo de cancelación* muestra la probabilidad, el nivel de riesgo, la acción recomendada y qué cambios reducirían el riesgo.
- **Evaluar varias reservas:** permite descargar una plantilla de Excel con listas desplegables, diligenciarla con todas las reservas del día y subirla para calcular el riesgo de todas a la vez. Los resultados se descargan en Excel, coloreados por nivel de riesgo.
- **Sobre el modelo:** métricas del modelo con datos de prueba, variables más importantes y significado de cada nivel de riesgo.

## Archivos

| Archivo | Contenido |
|---|---|
| `app.py` | Aplicación en Streamlit |
| `modelo_cancelacion.pkl` | Modelo entrenado, exportado desde Google Colab |
| `configuracion_modelo.json` | Variables, opciones y rangos que usa la aplicación |
| `requirements.txt` | Librerías necesarias, con las mismas versiones usadas para entrenar el modelo |

## Autores

Juan Felipe Martínez Ortega · Juan José Ariza Quintero
