"""
Aplicación web: Simulador de riesgo de cancelación de reservas hoteleras
Proyecto aplicado - Metodología CRISP-DM (Fase 6: Despliegue)
Autores: Juan Felipe Martínez Ortega y Juan José Ariza Quintero
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Simulador de cancelaciones", page_icon="🏨", layout="wide")

AZUL, NARANJA, VERDE, AMARILLO, ROJO = "#2E6A8E", "#E07A3F", "#2E9E5B", "#E0A800", "#C8402F"


# ---------------------------------------------------------------
# Carga del modelo y de su configuración (una sola vez)
# ---------------------------------------------------------------
@st.cache_resource
def cargar_modelo():
    carpeta = Path(__file__).parent
    modelo = joblib.load(carpeta / "modelo_cancelacion.pkl")
    with open(carpeta / "configuracion_modelo.json", encoding="utf-8") as f:
        configuracion = json.load(f)
    return modelo, configuracion


modelo, config = cargar_modelo()
opciones, rangos = config["opciones"], config["rangos"]
COLUMNAS = config["numericas"] + config["binarias"] + config["categoricas"]

# ---------------------------------------------------------------
# Nombres en español
# ---------------------------------------------------------------
ETIQUETAS = {
    "hotel": {"City Hotel": "Hotel de ciudad", "Resort Hotel": "Resort"},
    "meal": {"BB": "Alojamiento y desayuno", "HB": "Media pensión", "FB": "Pensión completa", "SC": "Sin comidas"},
    "market_segment": {"Online TA": "Agencia de viajes online", "Offline TA/TO": "Agencia tradicional u operador",
                       "Groups": "Grupo", "Direct": "Reserva directa", "Corporate": "Corporativo",
                       "Complementary": "Cortesía", "Aviation": "Aerolínea"},
    "distribution_channel": {"TA/TO": "Agencias y operadores", "Direct": "Directo", "Corporate": "Corporativo",
                             "GDS": "Sistema global de distribución (GDS)"},
    "deposit_type": {"No Deposit": "Sin depósito", "Non Refund": "No reembolsable", "Refundable": "Reembolsable"},
    "customer_type": {"Transient": "Individual", "Transient-Party": "Individual asociado a otra reserva",
                      "Contract": "Contrato", "Group": "Grupo"},
    "pais": {"PRT": "Portugal", "GBR": "Reino Unido", "FRA": "Francia", "ESP": "España", "DEU": "Alemania",
             "ITA": "Italia", "IRL": "Irlanda", "BEL": "Bélgica", "BRA": "Brasil", "NLD": "Países Bajos",
             "Otros": "Otro país"},
}
NOMBRES_VARIABLES = {
    "lead_time": "Días de anticipación", "adr": "Tarifa por noche", "total_noches": "Número de noches",
    "total_huespedes": "Total de huéspedes", "mes_llegada": "Mes de llegada",
    "previous_cancellations": "Cancelaciones previas", "previous_bookings_not_canceled": "Reservas previas cumplidas",
    "booking_changes": "Cambios en la reserva", "days_in_waiting_list": "Días en lista de espera",
    "required_car_parking_spaces": "Parqueadero solicitado", "total_of_special_requests": "Solicitudes especiales",
    "is_repeated_guest": "Cliente repetido", "tiene_agente": "Reserva con agente",
    "tiene_empresa": "Reserva con empresa", "tiene_ninos": "Viaja con niños", "cancelo_antes": "Canceló antes",
    "hotel": "Hotel", "meal": "Plan de comidas", "market_segment": "Segmento", "distribution_channel": "Canal",
    "reserved_room_type": "Habitación", "deposit_type": "Depósito", "customer_type": "Tipo de cliente", "pais": "País",
}
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ---------------------------------------------------------------
# Valores iniciales y ejemplos rápidos
# ---------------------------------------------------------------
INICIAL = {
    "hotel": "City Hotel", "lead_time": 60, "mes": "Julio", "noches": 3, "adr": 100.0, "habitacion": "A",
    "comida": "BB", "adultos": 2, "ninos": 0, "bebes": 0, "parqueadero": 0, "solicitudes": 0, "cambios": 0,
    "espera": 0, "segmento": "Online TA", "canal": "TA/TO", "deposito": "No Deposit", "cliente": "Transient",
    "pais": "PRT", "agente": True, "empresa": False, "repetido": False, "cancel_prev": 0, "cumplidas_prev": 0,
}
EJEMPLOS = {
    "🔴 Riesgo alto": {"lead_time": 200, "segmento": "Groups", "deposito": "Non Refund"},
    "🟡 Riesgo medio": {"solicitudes": 1},
    "🟢 Riesgo bajo": {"hotel": "Resort Hotel", "lead_time": 15, "mes": "Enero", "segmento": "Direct",
                      "canal": "Direct", "agente": False, "pais": "GBR", "solicitudes": 2},
}


def cargar_valores(cambios=None):
    """Pone los valores iniciales (y los cambios de un ejemplo) en los campos del simulador."""
    valores = {**INICIAL, **(cambios or {})}
    for clave, valor in valores.items():
        st.session_state[clave] = valor


if "hotel" not in st.session_state:
    cargar_valores()


# ---------------------------------------------------------------
# Funciones de apoyo
# ---------------------------------------------------------------
def construir_reserva(v):
    """Convierte los datos del simulador en una fila con las variables que usó el modelo."""
    return {
        "lead_time": v["lead_time"], "adr": v["adr"], "total_noches": v["noches"],
        "total_huespedes": v["adultos"] + v["ninos"] + v["bebes"], "mes_llegada": MESES.index(v["mes"]) + 1,
        "previous_cancellations": v["cancel_prev"], "previous_bookings_not_canceled": v["cumplidas_prev"],
        "booking_changes": v["cambios"], "days_in_waiting_list": v["espera"],
        "required_car_parking_spaces": v["parqueadero"], "total_of_special_requests": v["solicitudes"],
        "is_repeated_guest": int(v["repetido"]), "tiene_agente": int(v["agente"]), "tiene_empresa": int(v["empresa"]),
        "tiene_ninos": int(v["ninos"] + v["bebes"] > 0), "cancelo_antes": int(v["cancel_prev"] > 0),
        "hotel": v["hotel"], "meal": v["comida"], "market_segment": v["segmento"], "distribution_channel": v["canal"],
        "reserved_room_type": v["habitacion"], "deposit_type": v["deposito"], "customer_type": v["cliente"],
        "pais": v["pais"],
    }


def predecir(filas):
    """Probabilidad de cancelación para una o varias reservas."""
    return modelo.predict_proba(pd.DataFrame(filas)[COLUMNAS])[:, 1]


def nivel_riesgo(p):
    if p >= 0.70:
        return "ALTO", ROJO, ("Solicitar un depósito o prepago, confirmar la reserva con el cliente "
                              "y tenerla en cuenta al decidir la sobreventa.")
    if p >= 0.40:
        return "MEDIO", AMARILLO, ("Enviar un recordatorio y ofrecer beneficios que aumenten el compromiso "
                                   "del cliente (por ejemplo, parqueadero o servicios adicionales).")
    return "BAJO", VERDE, "No se requiere ninguna acción adicional."


def lista(clave, variable, etiqueta):
    nombres = ETIQUETAS.get(variable, {})
    return st.selectbox(etiqueta, opciones[variable], key=clave, format_func=lambda c: nombres.get(c, f"Tipo {c}"))


def entero(clave, variable, etiqueta, ayuda=None, maximo=None):
    r = rangos[variable]
    return st.number_input(etiqueta, min_value=int(r["min"]), max_value=int(maximo or r["max"]),
                           step=1, key=clave, help=ayuda)


def nombre_columna(col):
    """Traduce las columnas del modelo (por ejemplo 'deposit_type_Non Refund') a un nombre legible."""
    for variable in config["categoricas"]:
        if col.startswith(variable + "_"):
            categoria = col[len(variable) + 1:]
            return f"{NOMBRES_VARIABLES[variable]}: {ETIQUETAS.get(variable, {}).get(categoria, categoria)}"
    return NOMBRES_VARIABLES.get(col, col)


def mostrar_resultado(valores, prob):
    """Velocímetro, nivel de riesgo y escenarios de cambio para la reserva actual."""
    nivel, color, accion = nivel_riesgo(prob)

    # Indicador tipo velocímetro
    indicador = go.Figure(go.Indicator(
        mode="gauge+number", value=prob * 100, number={"suffix": "%", "valueformat": ".1f", "font": {"color": color, "size": 44}},
        title={"text": "Probabilidad de cancelación"},
        gauge={"axis": {"range": [0, 100], "tickvals": [0, 40, 70, 100]}, "bar": {"color": "#1E2933", "thickness": 0.25},
               "steps": [{"range": [0, 40], "color": "#D9F0E1"}, {"range": [40, 70], "color": "#FCEFC7"},
                         {"range": [70, 100], "color": "#F6D5D0"}]}))
    indicador.update_layout(height=260, margin=dict(l=35, r=45, t=50, b=10))
    st.plotly_chart(indicador, width="stretch")

    st.markdown(
        f"<div style='border-left:6px solid {color};padding:10px 14px;border-radius:6px;"
        f"background:rgba(128,128,128,0.08)'><b style='color:{color}'>Riesgo {nivel}</b><br>"
        f"<b>Acción recomendada:</b> {accion}</div>", unsafe_allow_html=True)

    # ¿Qué cambiaría el riesgo?
    st.subheader("¿Qué cambiaría el riesgo?")
    escenarios = {}
    if valores["parqueadero"] == 0:
        escenarios["Si pidiera parqueadero"] = {**valores, "parqueadero": 1}
    if valores["solicitudes"] < 5:
        escenarios["Si hiciera una solicitud especial más"] = {**valores, "solicitudes": valores["solicitudes"] + 1}
    if valores["segmento"] != "Direct":
        escenarios["Si reservara directamente con el hotel"] = {
            **valores, "segmento": "Direct", "canal": "Direct", "agente": False}
    if valores["deposito"] != "No Deposit":
        escenarios["Si no tuviera depósito"] = {**valores, "deposito": "No Deposit"}
    if valores["lead_time"] > 30:
        escenarios["Si reservara con 30 días de anticipación"] = {**valores, "lead_time": 30}
    if valores["cancel_prev"] > 0:
        escenarios["Si no tuviera cancelaciones previas"] = {**valores, "cancel_prev": 0}

    if escenarios:
        probs = predecir([construir_reserva(v) for v in escenarios.values()])
        cambio = pd.Series((probs - prob) * 100, index=list(escenarios))
        cambio = cambio[cambio.abs() >= 0.5].sort_values()   # solo cambios de al menos medio punto
    if not escenarios or cambio.empty:
        st.info("Con estos datos, ningún cambio individual modifica el riesgo de forma importante.")
    else:
        for escenario, x in cambio.items():
            color_cambio, flecha = (VERDE, "▼") if x < 0 else (ROJO, "▲")
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:6px 10px;margin-bottom:6px;"
                f"border-radius:6px;background:rgba(128,128,128,0.08)'><span>{escenario}</span>"
                f"<span style='color:{color_cambio};font-weight:600;white-space:nowrap'>"
                f"{flecha} {prob * 100 + x:.0f}% ({x:+.1f} pts)</span></div>", unsafe_allow_html=True)
        st.caption("Cada fila muestra cuál sería el riesgo si se modificara solo ese dato de la reserva.")


def mostrar_curva(valores, prob):
    """Riesgo de la reserva actual para distintos días de anticipación."""
    st.subheader("¿Cómo cambia el riesgo según los días de anticipación?")
    dias = list(range(0, 366, 5))
    curva = predecir([construir_reserva({**valores, "lead_time": d}) for d in dias]) * 100
    linea = go.Figure()
    linea.add_trace(go.Scatter(x=dias, y=curva, mode="lines", line=dict(color=AZUL, width=3), name="Riesgo"))
    linea.add_trace(go.Scatter(x=[valores["lead_time"]], y=[prob * 100], mode="markers", name="Reserva actual",
                               marker=dict(color=NARANJA, size=14, line=dict(color="white", width=2))))
    linea.add_hrect(y0=70, y1=100, fillcolor=ROJO, opacity=0.08, line_width=0)
    linea.add_hrect(y0=40, y1=70, fillcolor=AMARILLO, opacity=0.08, line_width=0)
    linea.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=40), yaxis=dict(range=[0, 100]),
                        xaxis_title="Días de anticipación", yaxis_title="Probabilidad de cancelación (%)",
                        legend=dict(orientation="h", y=1.1))
    st.plotly_chart(linea, width="stretch")
    st.caption("La curva mantiene todos los demás datos de la reserva y solo cambia los días de anticipación. "
               "El punto naranja es la reserva actual. La curva es escalonada porque el modelo se basa en "
               "árboles de decisión, que dividen las reservas por rangos de valores.")


# ---------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------
with st.sidebar:
    st.header("🏨 Acerca del modelo")
    st.write(f"**Modelo:** {config['modelo']}")
    st.write("Entrenado con reservas reales de dos hoteles en Portugal (2015–2017) siguiendo la metodología CRISP-DM.")
    m = config["metricas_prueba"]
    c1, c2 = st.columns(2)
    c1.metric("Recall", f"{m['Recall']:.0%}", help="Porcentaje de cancelaciones reales que el modelo detecta.")
    c2.metric("Precision", f"{m['Precision']:.0%}", help="Porcentaje de alertas que son cancelaciones reales.")
    c1.metric("F1", f"{m['F1']:.3f}", help="Equilibrio entre Recall y Precision.")
    c2.metric("AUC-ROC", f"{m['AUC-ROC']:.3f}", help="Capacidad de separar reservas canceladas y no canceladas.")
    st.divider()
    st.caption("Proyecto aplicado – Diplomado. Juan Felipe Martínez Ortega y Juan José Ariza Quintero.")

st.title("🏨 Simulador de riesgo de cancelación")
st.write("Modifique los datos de la reserva y el riesgo se **actualiza al instante**.")

tab_sim, tab_lote, tab_modelo = st.tabs(["🎛️ Simulador", "📋 Evaluar varias reservas", "📊 Cómo decide el modelo"])

# ===============================================================
# Pestaña 1: Simulador en tiempo real
# ===============================================================
with tab_sim:
    st.write("**Cargar un ejemplo:**")
    botones = st.columns(len(EJEMPLOS) + 1)
    for boton, (nombre, cambios) in zip(botones, EJEMPLOS.items()):
        boton.button(nombre, on_click=cargar_valores, args=(cambios,), width="stretch")
    botones[-1].button("↺ Restablecer", on_click=cargar_valores, width="stretch")

    izquierda, derecha = st.columns([3, 2], gap="large")

    with izquierda:
        t1, t2, t3 = st.tabs(["📅 Reserva", "👥 Huéspedes y solicitudes", "🧾 Canal y cliente"])
        with t1:
            a, b = st.columns(2)
            with a:
                lista("hotel", "hotel", "Hotel")
                st.slider("Días de anticipación", 0, 365, key="lead_time",
                          help="Días entre la fecha en que se hizo la reserva y la fecha de llegada.")
                st.select_slider("Mes de llegada", MESES, key="mes")
            with b:
                st.slider("Número de noches", 1, 21, key="noches")
                st.slider("Tarifa promedio por noche (€)", 0.0, 400.0, step=5.0, key="adr")
                lista("habitacion", "reserved_room_type", "Tipo de habitación")
                lista("comida", "meal", "Plan de comidas")
        with t2:
            a, b = st.columns(2)
            with a:
                st.number_input("Adultos", 0, 10, step=1, key="adultos")
                st.number_input("Niños", 0, 10, step=1, key="ninos")
                st.number_input("Bebés", 0, 10, step=1, key="bebes")
            with b:
                st.slider("Espacios de parqueadero", 0, 3, key="parqueadero")
                st.slider("Solicitudes especiales", 0, 5, key="solicitudes",
                          help="Por ejemplo: cama adicional, piso alto, cuna.")
                entero("cambios", "booking_changes", "Cambios en la reserva", maximo=10)
                entero("espera", "days_in_waiting_list", "Días en lista de espera")
        with t3:
            a, b = st.columns(2)
            with a:
                lista("segmento", "market_segment", "Segmento de mercado")
                lista("canal", "distribution_channel", "Canal de distribución")
                lista("deposito", "deposit_type", "Tipo de depósito")
                lista("cliente", "customer_type", "Tipo de cliente")
            with b:
                lista("pais", "pais", "País de origen")
                st.toggle("Reserva con agente de viajes", key="agente")
                st.toggle("Reserva con empresa", key="empresa")
                st.toggle("Cliente que ya se había hospedado", key="repetido")
                entero("cancel_prev", "previous_cancellations", "Cancelaciones previas", maximo=10)
                entero("cumplidas_prev", "previous_bookings_not_canceled", "Reservas previas cumplidas", maximo=20)

    valores = {k: st.session_state[k] for k in INICIAL}

    if valores["adultos"] + valores["ninos"] + valores["bebes"] == 0:
        derecha.error("La reserva debe tener al menos un huésped.")
    else:
        prob = float(predecir([construir_reserva(valores)])[0])
        with derecha:
            mostrar_resultado(valores, prob)
        mostrar_curva(valores, prob)

# ===============================================================
# Pestaña 2: Evaluar varias reservas
# ===============================================================
with tab_lote:
    st.write("Suba un archivo CSV con varias reservas y el modelo calculará el riesgo de cada una. "
             "Descargue la plantilla para ver el formato que debe tener el archivo.")
    plantilla = pd.DataFrame([construir_reserva(INICIAL),
                              construir_reserva({**INICIAL, **EJEMPLOS["🟢 Riesgo bajo"]})])[COLUMNAS]
    st.download_button("⬇️ Descargar plantilla CSV", plantilla.to_csv(index=False).encode("utf-8"),
                       "plantilla_reservas.csv", "text/csv")
    archivo = st.file_uploader("Archivo de reservas (CSV)", type="csv")
    if archivo is not None:
        datos = pd.read_csv(archivo)
        faltan = [c for c in COLUMNAS if c not in datos.columns]
        if faltan:
            st.error(f"Al archivo le faltan estas columnas: {', '.join(faltan)}")
        else:
            datos["Probabilidad (%)"] = (predecir(datos) * 100).round(1)
            datos["Riesgo"] = [nivel_riesgo(p / 100)[0] for p in datos["Probabilidad (%)"]]
            resumen = datos["Riesgo"].value_counts()
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 Riesgo alto", int(resumen.get("ALTO", 0)))
            c2.metric("🟡 Riesgo medio", int(resumen.get("MEDIO", 0)))
            c3.metric("🟢 Riesgo bajo", int(resumen.get("BAJO", 0)))
            st.dataframe(datos.sort_values("Probabilidad (%)", ascending=False), width="stretch")
            st.download_button("⬇️ Descargar resultados", datos.to_csv(index=False).encode("utf-8"),
                               "riesgo_reservas.csv", "text/csv")

# ===============================================================
# Pestaña 3: Cómo decide el modelo
# ===============================================================
with tab_modelo:
    st.write("Estas son las variables que más usa el modelo para decidir si una reserva tiene riesgo de "
             "cancelación. Una importancia alta significa que esa variable le ayuda mucho a separar las "
             "reservas que se cancelan de las que no.")
    nombres = [n.split("__")[1] for n in modelo.named_steps["preparacion"].get_feature_names_out()]
    importancias = pd.Series(modelo.named_steps["modelo"].feature_importances_, index=nombres)
    top = importancias.sort_values(ascending=False).head(12).sort_values()
    grafica = go.Figure(go.Bar(x=top.values, y=[nombre_columna(c) for c in top.index], orientation="h",
                               marker_color=AZUL, text=[f"{v:.3f}" for v in top.values], textposition="outside"))
    grafica.update_layout(height=480, margin=dict(l=10, r=40, t=10, b=40), xaxis_title="Importancia relativa")
    st.plotly_chart(grafica, width="stretch")
    st.info("**Cómo leer el resultado:** el modelo calcula una probabilidad de cancelación entre 0% y 100%. "
            "Riesgo **bajo**: menos de 40%. Riesgo **medio**: de 40% a 70%. Riesgo **alto**: 70% o más.")

st.divider()
st.caption("Herramienta con fines académicos. El modelo se entrenó con datos de 2015 a 2017 de dos hoteles en "
           "Portugal; para uso real debe reentrenarse con datos recientes del hotel.")
