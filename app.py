"""
Aplicación web: Predicción de cancelación de reservas hoteleras
Proyecto aplicado - Metodología CRISP-DM (Fase 6: Despliegue)
Autores: Juan Felipe Martínez Ortega y Juan José Ariza Quintero
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------
st.set_page_config(page_title="Riesgo de cancelación de reservas", page_icon="🏨", layout="wide")


# ---------------------------------------------------------------
# Carga del modelo y de su configuración (se hace una sola vez)
# ---------------------------------------------------------------
@st.cache_resource
def cargar_modelo():
    carpeta = Path(__file__).parent   # carpeta donde están app.py y los archivos del modelo
    modelo = joblib.load(carpeta / "modelo_cancelacion.pkl")
    with open(carpeta / "configuracion_modelo.json", encoding="utf-8") as f:
        configuracion = json.load(f)
    return modelo, configuracion


modelo, config = cargar_modelo()
opciones = config["opciones"]
rangos = config["rangos"]

# ---------------------------------------------------------------
# Nombres en español para las categorías del modelo
# ---------------------------------------------------------------
ETIQUETAS = {
    "hotel": {"City Hotel": "Hotel de ciudad", "Resort Hotel": "Resort"},
    "meal": {"BB": "Alojamiento y desayuno", "HB": "Media pensión",
             "FB": "Pensión completa", "SC": "Sin comidas"},
    "market_segment": {"Online TA": "Agencia de viajes online", "Offline TA/TO": "Agencia tradicional u operador",
                       "Groups": "Grupo", "Direct": "Reserva directa", "Corporate": "Corporativo",
                       "Complementary": "Cortesía", "Aviation": "Aerolínea"},
    "distribution_channel": {"TA/TO": "Agencias y operadores", "Direct": "Directo",
                             "Corporate": "Corporativo", "GDS": "Sistema global de distribución (GDS)"},
    "deposit_type": {"No Deposit": "Sin depósito", "Non Refund": "No reembolsable", "Refundable": "Reembolsable"},
    "customer_type": {"Transient": "Individual", "Transient-Party": "Individual asociado a otra reserva",
                      "Contract": "Contrato", "Group": "Grupo"},
    "pais": {"PRT": "Portugal", "GBR": "Reino Unido", "FRA": "Francia", "ESP": "España", "DEU": "Alemania",
             "ITA": "Italia", "IRL": "Irlanda", "BEL": "Bélgica", "BRA": "Brasil", "NLD": "Países Bajos",
             "Otros": "Otro país"},
}
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def lista(variable, etiqueta, por_defecto=None):
    """Lista desplegable que muestra el nombre en español y devuelve el código que entiende el modelo."""
    codigos = opciones[variable]
    nombres = ETIQUETAS.get(variable, {})
    indice = codigos.index(por_defecto) if por_defecto in codigos else 0
    return st.selectbox(etiqueta, codigos, index=indice, format_func=lambda c: nombres.get(c, f"Tipo {c}"))


def numero(variable, etiqueta, valor=None, ayuda=None):
    """Campo numérico limitado al rango de valores que el modelo conoce."""
    r = rangos[variable]
    inicial = int(r["mediana"] if valor is None else valor)
    return st.number_input(etiqueta, min_value=int(r["min"]), max_value=int(r["max"]),
                           value=inicial, step=1, help=ayuda)


# ---------------------------------------------------------------
# Barra lateral: información del modelo
# ---------------------------------------------------------------
with st.sidebar:
    st.header("Acerca del modelo")
    st.write(f"**Modelo:** {config['modelo']}")
    st.write("Entrenado con reservas reales de dos hoteles en Portugal (2015–2017), "
             "siguiendo la metodología CRISP-DM.")
    st.subheader("Desempeño con datos nuevos")
    m = config["metricas_prueba"]
    c1, c2 = st.columns(2)
    c1.metric("Recall", f"{m['Recall']:.0%}", help="Porcentaje de cancelaciones reales que el modelo detecta.")
    c2.metric("Precision", f"{m['Precision']:.0%}", help="Porcentaje de alertas que son cancelaciones reales.")
    c1.metric("F1", f"{m['F1']:.3f}")
    c2.metric("AUC-ROC", f"{m['AUC-ROC']:.3f}")
    st.divider()
    st.caption("Proyecto aplicado – Diplomado. Juan Felipe Martínez Ortega y Juan José Ariza Quintero.")

# ---------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------
st.title("🏨 Riesgo de cancelación de reservas")
st.write("Ingrese los datos de una reserva y el modelo estimará la **probabilidad de que sea cancelada**, "
         "junto con una acción recomendada para el hotel.")

# ---------------------------------------------------------------
# Formulario con los datos de la reserva
# ---------------------------------------------------------------
with st.form("reserva"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📅 Reserva")
        hotel = lista("hotel", "Hotel")
        lead_time = numero("lead_time", "Días de anticipación", 60,
                           "Días entre la fecha en que se hizo la reserva y la fecha de llegada.")
        mes = st.selectbox("Mes de llegada", MESES, index=6)
        total_noches = numero("total_noches", "Número de noches", 3)
        adr = st.number_input("Tarifa promedio por noche (€)", min_value=0.0,
                              max_value=float(rangos["adr"]["max"]), value=100.0, step=5.0)
        tipo_habitacion = lista("reserved_room_type", "Tipo de habitación reservada", "A")
        comida = lista("meal", "Plan de comidas", "BB")

    with col2:
        st.subheader("👥 Huéspedes y solicitudes")
        adultos = st.number_input("Adultos", min_value=0, max_value=10, value=2, step=1)
        ninos = st.number_input("Niños", min_value=0, max_value=10, value=0, step=1)
        bebes = st.number_input("Bebés", min_value=0, max_value=10, value=0, step=1)
        parqueadero = numero("required_car_parking_spaces", "Espacios de parqueadero solicitados", 0)
        solicitudes = numero("total_of_special_requests", "Solicitudes especiales", 0,
                             "Por ejemplo: cama adicional, piso alto, cuna.")
        cambios = numero("booking_changes", "Cambios realizados a la reserva", 0)
        espera = numero("days_in_waiting_list", "Días en lista de espera", 0)

    with col3:
        st.subheader("🧾 Canal y cliente")
        segmento = lista("market_segment", "Segmento de mercado", "Online TA")
        canal = lista("distribution_channel", "Canal de distribución", "TA/TO")
        deposito = lista("deposit_type", "Tipo de depósito", "No Deposit")
        tipo_cliente = lista("customer_type", "Tipo de cliente", "Transient")
        pais = lista("pais", "País de origen", "PRT")
        tiene_agente = st.checkbox("Reserva hecha por agente de viajes", value=True)
        tiene_empresa = st.checkbox("Reserva hecha por una empresa", value=False)
        repetido = st.checkbox("Cliente que ya se había hospedado", value=False)
        cancelaciones_previas = numero("previous_cancellations", "Cancelaciones previas del cliente", 0)
        reservas_previas = numero("previous_bookings_not_canceled", "Reservas previas no canceladas", 0)

    enviar = st.form_submit_button("Calcular riesgo de cancelación", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# Predicción
# ---------------------------------------------------------------
if enviar:
    total_huespedes = adultos + ninos + bebes
    if total_huespedes == 0:
        st.error("La reserva debe tener al menos un huésped.")
        st.stop()

    # Se arma la reserva con las mismas variables que se usaron para entrenar el modelo
    reserva = pd.DataFrame([{
        "lead_time": lead_time, "adr": adr, "total_noches": total_noches,
        "total_huespedes": total_huespedes, "mes_llegada": MESES.index(mes) + 1,
        "previous_cancellations": cancelaciones_previas,
        "previous_bookings_not_canceled": reservas_previas,
        "booking_changes": cambios, "days_in_waiting_list": espera,
        "required_car_parking_spaces": parqueadero, "total_of_special_requests": solicitudes,
        "is_repeated_guest": int(repetido), "tiene_agente": int(tiene_agente),
        "tiene_empresa": int(tiene_empresa), "tiene_ninos": int(ninos + bebes > 0),
        "cancelo_antes": int(cancelaciones_previas > 0),
        "hotel": hotel, "meal": comida, "market_segment": segmento, "distribution_channel": canal,
        "reserved_room_type": tipo_habitacion, "deposit_type": deposito,
        "customer_type": tipo_cliente, "pais": pais,
    }])[config["numericas"] + config["binarias"] + config["categoricas"]]

    probabilidad = float(modelo.predict_proba(reserva)[0, 1])

    if probabilidad >= 0.70:
        nivel, mostrar = "ALTO", st.error
        accion = ("Solicitar un depósito o prepago y confirmar la reserva con el cliente. "
                  "Tener en cuenta esta reserva al decidir la sobreventa.")
    elif probabilidad >= 0.40:
        nivel, mostrar = "MEDIO", st.warning
        accion = ("Enviar un recordatorio y ofrecer beneficios que aumenten el compromiso del cliente "
                  "(por ejemplo, parqueadero o servicios adicionales).")
    else:
        nivel, mostrar = "BAJO", st.success
        accion = "No se requiere ninguna acción adicional."

    st.divider()
    st.subheader("Resultado")
    r1, r2 = st.columns([1, 2])
    with r1:
        st.metric("Probabilidad de cancelación", f"{probabilidad:.1%}")
        st.progress(probabilidad)
    with r2:
        mostrar(f"**Riesgo {nivel}**\n\n**Acción recomendada:** {accion}")

    st.caption(f"El modelo clasifica como cancelación toda reserva con probabilidad mayor al "
               f"{config['umbral']:.0%}. Niveles de riesgo: bajo (menos de 40%), medio (40% a 70%) "
               f"y alto (70% o más).")

st.divider()
st.caption("Herramienta con fines académicos. El modelo se entrenó con datos de 2015 a 2017 de dos hoteles "
           "en Portugal; para uso real debe reentrenarse con datos recientes del hotel.")
