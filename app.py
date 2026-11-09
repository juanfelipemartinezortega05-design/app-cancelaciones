"""
Aplicación web: Riesgo de cancelación de reservas hoteleras
Proyecto aplicado - Metodología CRISP-DM (Fase 6: Despliegue)
Autores: Juan Felipe Martínez Ortega y Juan José Ariza Quintero
"""
import io
import json
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

st.set_page_config(page_title="Riesgo de cancelación de reservas", page_icon="🏨", layout="wide",
                   initial_sidebar_state="collapsed")

AZUL, AZUL_OSCURO = "#2E6A8E", "#1D3557"
VERDE, AMARILLO, ROJO = "#2E9E5B", "#D99A00", "#C8402F"

# ---------------------------------------------------------------
# Estilo visual de la página
# ---------------------------------------------------------------
st.markdown(f"""
<style>
    .block-container {{padding-top: 1.5rem; max-width: 1200px;}}
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {{display: none;}}
    .portada {{background: linear-gradient(120deg, {AZUL_OSCURO} 0%, {AZUL} 100%); color: white;
              padding: 28px 32px; border-radius: 16px; margin-bottom: 18px;}}
    .portada h1 {{color: white; margin: 0 0 6px 0; font-size: 2.1rem;}}
    .portada p {{color: #DCE8F2; margin: 0; font-size: 1.05rem;}}
    .paso {{display: flex; align-items: center; gap: 10px; margin-bottom: 4px;}}
    .paso .numero {{background: {AZUL}; color: white; border-radius: 50%; width: 30px; height: 30px;
                   display: flex; align-items: center; justify-content: center; font-weight: 700;}}
    .paso .titulo {{font-size: 1.15rem; font-weight: 700; color: {AZUL_OSCURO};}}
    .ayuda {{color: #6B7785; font-size: 0.9rem; margin: 0 0 10px 40px;}}
    .resultado {{border-radius: 14px; padding: 22px 26px; color: white;}}
    .resultado .etiqueta {{font-size: 0.95rem; opacity: 0.9;}}
    .resultado .valor {{font-size: 3rem; font-weight: 800; line-height: 1.1;}}
    .resultado .nivel {{font-size: 1.3rem; font-weight: 700;}}
    .accion {{border-left: 5px solid {AZUL}; background: #F2F6FA; padding: 14px 18px; border-radius: 8px;
             color: #1E2933; margin-top: 12px;}}
    .escenario {{display: flex; justify-content: space-between; padding: 9px 14px; margin-bottom: 6px;
                border-radius: 8px; background: #F2F6FA; color: #1E2933;}}
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button,
    div.stDownloadButton > button {{background: {AZUL}; border-color: {AZUL}; color: white; font-weight: 600;}}
    div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button:hover,
    div.stDownloadButton > button:hover {{background: {AZUL_OSCURO}; border-color: {AZUL_OSCURO}; color: white;}}
</style>
""", unsafe_allow_html=True)


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
# Nombres en español para las categorías del modelo
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
    "reserved_room_type": {c: f"Tipo {c}" for c in opciones["reserved_room_type"]},
}
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
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


# ---------------------------------------------------------------
# Funciones del modelo
# ---------------------------------------------------------------
def construir_reserva(v):
    """Convierte los datos de una reserva en las variables que usó el modelo en el entrenamiento."""
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
    """Nivel de riesgo, color y acción recomendada según la probabilidad."""
    if p >= 0.70:
        return "Alto", ROJO, ("Solicitar un depósito o prepago, confirmar la reserva con el cliente y tenerla "
                              "en cuenta al decidir la sobreventa.")
    if p >= 0.40:
        return "Medio", AMARILLO, ("Enviar un recordatorio y ofrecer beneficios que aumenten el compromiso del "
                                   "cliente, como parqueadero o servicios adicionales.")
    return "Bajo", VERDE, "No se requiere ninguna acción adicional."


# ---------------------------------------------------------------
# Componentes visuales
# ---------------------------------------------------------------
def paso(numero, titulo, ayuda):
    st.markdown(f"<div class='paso'><div class='numero'>{numero}</div><div class='titulo'>{titulo}</div></div>"
                f"<p class='ayuda'>{ayuda}</p>", unsafe_allow_html=True)


def lista(variable, etiqueta, por_defecto, ayuda=None):
    codigos = opciones[variable]
    nombres = ETIQUETAS.get(variable, {})
    return st.selectbox(etiqueta, codigos, index=codigos.index(por_defecto),
                        format_func=lambda c: nombres.get(c, c), help=ayuda)


def mostrar_resultado(valores, prob):
    nivel, color, accion = nivel_riesgo(prob)
    izquierda, derecha = st.columns([2, 3], gap="large")

    with izquierda:
        st.markdown(f"<div class='resultado' style='background:{color}'>"
                    f"<div class='etiqueta'>Probabilidad de cancelación</div>"
                    f"<div class='valor'>{prob:.1%}</div>"
                    f"<div class='nivel'>Riesgo {nivel.lower()}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='accion'><b>Acción recomendada</b><br>{accion}</div>", unsafe_allow_html=True)

    with derecha:
        indicador = go.Figure(go.Indicator(
            mode="gauge", value=prob * 100,
            gauge={"axis": {"range": [0, 100], "tickvals": [0, 40, 70, 100], "ticksuffix": "%"},
                   "bar": {"color": AZUL_OSCURO, "thickness": 0.3},
                   "steps": [{"range": [0, 40], "color": "#D9F0E1"}, {"range": [40, 70], "color": "#FCEFC7"},
                             {"range": [70, 100], "color": "#F6D5D0"}]}))
        indicador.update_layout(height=210, margin=dict(l=40, r=50, t=25, b=20))
        st.plotly_chart(indicador, width="stretch", config={"displayModeBar": False})

        # Qué cambios reducirían el riesgo de esta reserva
        escenarios = {}
        if valores["parqueadero"] == 0:
            escenarios["Si el cliente pidiera parqueadero"] = {**valores, "parqueadero": 1}
        if valores["solicitudes"] < 5:
            escenarios["Si hiciera una solicitud especial más"] = {**valores, "solicitudes": valores["solicitudes"] + 1}
        if valores["segmento"] != "Direct":
            escenarios["Si reservara directamente con el hotel"] = {
                **valores, "segmento": "Direct", "canal": "Direct", "agente": False}
        if valores["deposito"] != "No Deposit":
            escenarios["Si la reserva no tuviera depósito"] = {**valores, "deposito": "No Deposit"}
        if valores["lead_time"] > 30:
            escenarios["Si reservara con 30 días de anticipación"] = {**valores, "lead_time": 30}

        if escenarios:
            nuevas = predecir([construir_reserva(v) for v in escenarios.values()])
            cambios = sorted([(n, p) for n, p in zip(escenarios, nuevas) if p < prob - 0.005], key=lambda x: x[1])
            if cambios:
                st.markdown("**¿Qué reduciría el riesgo de esta reserva?**")
                for nombre, p in cambios[:3]:
                    st.markdown(f"<div class='escenario'><span>{nombre}</span>"
                                f"<b style='color:{VERDE}'>▼ {p:.1%}</b></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------
# Plantilla de Excel para evaluar varias reservas
# ---------------------------------------------------------------
SI_NO = ["Sí", "No"]
PLANTILLA = [
    # (encabezado, clave interna, tipo, opciones, descripción)
    ("Código de reserva", "codigo", "texto", None, "Identificador de la reserva en el sistema del hotel (opcional)."),
    ("Hotel", "hotel", "lista", "hotel", "Hotel de ciudad o Resort."),
    ("Días de anticipación", "lead_time", "numero", None, "Días entre la fecha de la reserva y la fecha de llegada."),
    ("Mes de llegada", "mes", "lista", MESES, "Mes en que llega el cliente."),
    ("Número de noches", "noches", "numero", None, "Total de noches de la estadía."),
    ("Tarifa por noche (€)", "adr", "numero", None, "Precio promedio por noche."),
    ("Tipo de habitación", "habitacion", "lista", "reserved_room_type", "Categoría de habitación reservada."),
    ("Plan de comidas", "comida", "lista", "meal", "Comidas incluidas en la reserva."),
    ("Adultos", "adultos", "numero", None, "Número de adultos."),
    ("Niños", "ninos", "numero", None, "Número de niños."),
    ("Bebés", "bebes", "numero", None, "Número de bebés."),
    ("Espacios de parqueadero", "parqueadero", "numero", None, "Parqueaderos solicitados por el cliente."),
    ("Solicitudes especiales", "solicitudes", "numero", None, "Cama adicional, piso alto, cuna, etc."),
    ("Cambios en la reserva", "cambios", "numero", None, "Veces que el cliente modificó la reserva."),
    ("Días en lista de espera", "espera", "numero", None, "Días que esperó la confirmación del hotel."),
    ("Segmento de mercado", "segmento", "lista", "market_segment", "Tipo de venta."),
    ("Canal de distribución", "canal", "lista", "distribution_channel", "Medio por el que llegó la reserva."),
    ("Tipo de depósito", "deposito", "lista", "deposit_type", "Garantía pagada por el cliente."),
    ("Tipo de cliente", "cliente", "lista", "customer_type", "Clasificación del cliente."),
    ("País de origen", "pais", "lista", "pais", "País del cliente."),
    ("Reserva con agente", "agente", "lista", SI_NO, "¿La reserva la gestionó un agente de viajes?"),
    ("Reserva con empresa", "empresa", "lista", SI_NO, "¿La reserva la hizo una empresa?"),
    ("Cliente repetido", "repetido", "lista", SI_NO, "¿El cliente ya se había hospedado en el hotel?"),
    ("Cancelaciones previas", "cancel_prev", "numero", None, "Reservas anteriores que el cliente canceló."),
    ("Reservas previas cumplidas", "cumplidas_prev", "numero", None, "Reservas anteriores que el cliente cumplió."),
]
EJEMPLO_1 = {"codigo": "R-0001", "hotel": "City Hotel", "lead_time": 60, "mes": "Julio", "noches": 3, "adr": 100,
             "habitacion": "A", "comida": "BB", "adultos": 2, "ninos": 0, "bebes": 0, "parqueadero": 0,
             "solicitudes": 0, "cambios": 0, "espera": 0, "segmento": "Online TA", "canal": "TA/TO",
             "deposito": "No Deposit", "cliente": "Transient", "pais": "PRT", "agente": True, "empresa": False,
             "repetido": False, "cancel_prev": 0, "cumplidas_prev": 0}
EJEMPLO_2 = {**EJEMPLO_1, "codigo": "R-0002", "hotel": "Resort Hotel", "lead_time": 15, "mes": "Enero",
             "segmento": "Direct", "canal": "Direct", "agente": False, "pais": "GBR", "solicitudes": 2}


def opciones_columna(opcion):
    """Lista de textos válidos (en español) para una columna con lista desplegable."""
    if isinstance(opcion, list):
        return opcion
    return [ETIQUETAS[opcion].get(c, c) for c in opciones[opcion]]


def a_texto(opcion, valor):
    """Convierte un valor interno al texto que se muestra en la plantilla."""
    if opcion is SI_NO:
        return "Sí" if valor else "No"
    if isinstance(opcion, str):
        return ETIQUETAS[opcion].get(valor, valor)
    return valor


@st.cache_data
def crear_plantilla():
    """Crea la plantilla de Excel con columnas, listas desplegables e instrucciones."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Reservas"
    listas = libro.create_sheet("Listas")
    instrucciones = libro.create_sheet("Instrucciones")

    relleno = PatternFill("solid", fgColor=AZUL_OSCURO[1:])
    for col, (titulo, clave, tipo, opcion, _) in enumerate(PLANTILLA, start=1):
        celda = hoja.cell(row=1, column=col, value=titulo)
        celda.font, celda.fill = Font(bold=True, color="FFFFFF"), relleno
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        letra = celda.column_letter
        hoja.column_dimensions[letra].width = max(16, len(titulo) + 4)
        for fila, ejemplo in enumerate([EJEMPLO_1, EJEMPLO_2], start=2):
            hoja.cell(row=fila, column=col, value=a_texto(opcion, ejemplo[clave]))
        if tipo == "lista":
            valores = opciones_columna(opcion)
            for i, valor in enumerate(valores, start=1):
                listas.cell(row=i, column=col, value=valor)
            validacion = DataValidation(type="list", formula1=f"=Listas!${letra}$1:${letra}${len(valores)}",
                                        showErrorMessage=True, errorTitle="Valor no válido",
                                        error="Elija una opción de la lista.")
        elif tipo == "numero":
            validacion = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0",
                                        showErrorMessage=True, errorTitle="Valor no válido",
                                        error="Escriba un número mayor o igual a 0.")
        else:
            continue
        hoja.add_data_validation(validacion)
        validacion.add(f"{letra}2:{letra}5000")
    hoja.row_dimensions[1].height = 34
    hoja.freeze_panes = "B2"
    listas.sheet_state = "hidden"

    instrucciones.column_dimensions["A"].width = 30
    instrucciones.column_dimensions["B"].width = 75
    instrucciones["A1"] = "Cómo usar esta plantilla"
    instrucciones["A1"].font = Font(bold=True, size=14, color=AZUL_OSCURO[1:])
    pasos = ["1. En la hoja 'Reservas', escriba una reserva por fila. Las dos primeras filas son ejemplos y "
             "puede borrarlas.",
             "2. En las columnas con lista desplegable, elija una de las opciones.",
             "3. Guarde el archivo y súbalo en la aplicación, en la sección 'Evaluar varias reservas'."]
    for i, texto in enumerate(pasos, start=2):
        instrucciones.cell(row=i, column=1, value=texto)
    instrucciones.cell(row=6, column=1, value="Columna").font = Font(bold=True)
    instrucciones.cell(row=6, column=2, value="Qué debe escribir").font = Font(bold=True)
    for i, (titulo, _, _, _, descripcion) in enumerate(PLANTILLA, start=7):
        instrucciones.cell(row=i, column=1, value=titulo)
        instrucciones.cell(row=i, column=2, value=descripcion)

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def leer_plantilla(archivo):
    """Lee la plantilla diligenciada y convierte cada fila en una reserva para el modelo."""
    datos = pd.read_excel(archivo, sheet_name="Reservas").dropna(how="all")
    faltan = [titulo for titulo, *_ in PLANTILLA if titulo not in datos.columns]
    if faltan:
        raise ValueError(f"Al archivo le faltan estas columnas: {', '.join(faltan)}")

    traducciones = {clave: {v: k for k, v in ETIQUETAS[opcion].items()}
                    for _, clave, _, opcion, _ in PLANTILLA if isinstance(opcion, str)}
    reservas, errores = [], []
    for indice, fila in datos.iterrows():
        try:
            v = {}
            for titulo, clave, tipo, opcion, _ in PLANTILLA:
                valor = fila[titulo]
                if clave == "codigo":
                    v[clave] = "" if pd.isna(valor) else str(valor)
                elif pd.isna(valor):
                    raise ValueError(f"falta el dato '{titulo}'")
                elif tipo == "numero":
                    v[clave] = float(valor)
                elif opcion is SI_NO:
                    v[clave] = str(valor).strip().lower() in ("sí", "si")
                elif opcion is MESES:
                    if valor not in MESES:
                        raise ValueError(f"'{valor}' no es un mes válido")
                    v[clave] = valor
                else:
                    if valor not in traducciones[clave]:
                        raise ValueError(f"'{valor}' no es una opción válida de '{titulo}'")
                    v[clave] = traducciones[clave][valor]
            if v["adultos"] + v["ninos"] + v["bebes"] == 0:
                raise ValueError("la reserva no tiene huéspedes")
            reservas.append((fila, v))
        except ValueError as e:
            errores.append(f"Fila {indice + 2}: {e}")
    return reservas, errores


def excel_resultados(tabla):
    """Archivo de Excel con los resultados, coloreado según el nivel de riesgo."""
    salida = io.BytesIO()
    tabla.to_excel(salida, index=False, sheet_name="Resultados")
    libro = load_workbook(salida)
    hoja = libro["Resultados"]
    colores = {"Alto": "F6D5D0", "Medio": "FCEFC7", "Bajo": "D9F0E1"}
    col_riesgo = list(tabla.columns).index("Nivel de riesgo")
    for celda in hoja[1]:
        celda.font, celda.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor=AZUL_OSCURO[1:])
        celda.alignment = Alignment(wrap_text=True, vertical="center")
        hoja.column_dimensions[celda.column_letter].width = max(14, min(len(str(celda.value)) + 4, 40))
    for fila in hoja.iter_rows(min_row=2):
        color = colores.get(fila[col_riesgo].value)
        if color:
            for celda in fila[-3:]:
                celda.fill = PatternFill("solid", fgColor=color)
    hoja.freeze_panes = "B2"
    final = io.BytesIO()
    libro.save(final)
    return final.getvalue()


# ---------------------------------------------------------------
# Encabezado y navegación
# ---------------------------------------------------------------
st.markdown("<div class='portada'><h1>🏨 Riesgo de cancelación de reservas</h1>"
            "<p>Ingrese los datos de una reserva y conozca su probabilidad de cancelación "
            "y la acción recomendada para el hotel.</p></div>", unsafe_allow_html=True)

SECCIONES = ["🔎 Evaluar una reserva", "📂 Evaluar varias reservas", "📊 Sobre el modelo"]
seccion = st.segmented_control("Sección", SECCIONES, default=SECCIONES[0], label_visibility="collapsed")
seccion = seccion or SECCIONES[0]
st.write("")

# ===============================================================
# Sección 1: Evaluar una reserva
# ===============================================================
if seccion == SECCIONES[0]:
    with st.form("reserva", border=False):
        with st.container(border=True):
            paso(1, "Datos de la reserva", "Información básica: hotel, fechas, duración y tarifa.")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                hotel = lista("hotel", "Hotel", "City Hotel")
                comida = lista("meal", "Plan de comidas", "BB")
            with c2:
                lead_time = st.number_input("Días de anticipación", 0, int(rangos["lead_time"]["max"]), 60,
                                            help="Días entre la fecha en que se hizo la reserva y la llegada.")
                mes = st.selectbox("Mes de llegada", MESES, index=6)
            with c3:
                noches = st.number_input("Número de noches", 0, int(rangos["total_noches"]["max"]), 3)
                habitacion = lista("reserved_room_type", "Tipo de habitación", "A",
                                   "Categoría de habitación. Las letras son las que usa el hotel.")
            with c4:
                adr = st.number_input("Tarifa por noche (€)", 0.0, float(rangos["adr"]["max"]), 100.0, step=5.0)

        with st.container(border=True):
            paso(2, "Huéspedes y solicitudes", "Quiénes viajan y qué pidieron. Las solicitudes y el parqueadero "
                                               "muestran el compromiso del cliente con su viaje.")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                adultos = st.number_input("Adultos", 0, 10, 2)
                parqueadero = st.number_input("Espacios de parqueadero", 0, 8, 0)
            with c2:
                ninos = st.number_input("Niños", 0, 10, 0)
                solicitudes = st.number_input("Solicitudes especiales", 0, 5, 0,
                                              help="Por ejemplo: cama adicional, piso alto o cuna.")
            with c3:
                bebes = st.number_input("Bebés", 0, 10, 0)
                cambios = st.number_input("Cambios en la reserva", 0, 20, 0,
                                          help="Veces que el cliente modificó la reserva.")
            with c4:
                espera = st.number_input("Días en lista de espera", 0, int(rangos["days_in_waiting_list"]["max"]), 0,
                                         help="Días que la reserva esperó la confirmación del hotel.")

        with st.container(border=True):
            paso(3, "Canal de venta y cliente", "Cómo llegó la reserva y qué historial tiene el cliente.")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                segmento = lista("market_segment", "Segmento de mercado", "Online TA")
                canal = lista("distribution_channel", "Canal de distribución", "TA/TO")
            with c2:
                deposito = lista("deposit_type", "Tipo de depósito", "No Deposit")
                cliente = lista("customer_type", "Tipo de cliente", "Transient")
            with c3:
                pais = lista("pais", "País de origen", "PRT")
                cancel_prev = st.number_input("Cancelaciones previas", 0, 30, 0)
            with c4:
                cumplidas_prev = st.number_input("Reservas previas cumplidas", 0, 80, 0)
            c1, c2, c3 = st.columns(3)
            agente = c1.toggle("Reserva con agente de viajes", value=True)
            empresa = c2.toggle("Reserva con empresa", value=False)
            repetido = c3.toggle("Cliente que ya se había hospedado", value=False)

        calcular = st.form_submit_button("Calcular riesgo de cancelación", type="primary", width="stretch")

    if calcular:
        valores = dict(hotel=hotel, comida=comida, lead_time=lead_time, mes=mes, noches=noches,
                       habitacion=habitacion, adr=adr, adultos=adultos, ninos=ninos, bebes=bebes,
                       parqueadero=parqueadero, solicitudes=solicitudes, cambios=cambios, espera=espera,
                       segmento=segmento, canal=canal, deposito=deposito, cliente=cliente, pais=pais,
                       cancel_prev=cancel_prev, cumplidas_prev=cumplidas_prev, agente=agente, empresa=empresa,
                       repetido=repetido)
        if adultos + ninos + bebes == 0:
            st.error("La reserva debe tener al menos un huésped.")
        else:
            prob = float(predecir([construir_reserva(valores)])[0])
            st.write("")
            with st.container(border=True):
                paso("✓", "Resultado", "Probabilidad estimada por el modelo y acción sugerida para el hotel.")
                mostrar_resultado(valores, prob)

# ===============================================================
# Sección 2: Evaluar varias reservas
# ===============================================================
elif seccion == SECCIONES[1]:
    with st.container(border=True):
        paso(1, "Descargue la plantilla de Excel",
             "Tiene una columna por cada dato de la reserva, listas desplegables para elegir las opciones "
             "y una hoja de instrucciones. Escriba una reserva por fila.")
        st.download_button("⬇️ Descargar plantilla de Excel", crear_plantilla(), "plantilla_reservas.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.container(border=True):
        paso(2, "Suba la plantilla diligenciada", "El modelo calculará el riesgo de todas las reservas a la vez.")
        archivo = st.file_uploader("Plantilla diligenciada", type="xlsx", label_visibility="collapsed")

    if archivo is not None:
        try:
            reservas, errores = leer_plantilla(archivo)
        except ValueError as e:
            st.error(str(e))
            reservas, errores = [], []

        if errores:
            with st.expander(f"⚠️ {len(errores)} fila(s) con errores no se evaluaron"):
                st.write("\n".join(f"- {e}" for e in errores))

        if reservas:
            probs = predecir([construir_reserva(v) for _, v in reservas])
            tabla = pd.DataFrame([fila for fila, _ in reservas]).reset_index(drop=True)
            tabla["Probabilidad de cancelación (%)"] = [round(float(p) * 100, 1) for p in probs]
            tabla["Nivel de riesgo"] = [nivel_riesgo(p)[0] for p in probs]
            tabla["Acción recomendada"] = [nivel_riesgo(p)[2] for p in probs]
            tabla = tabla.sort_values("Probabilidad de cancelación (%)", ascending=False)

            with st.container(border=True):
                paso(3, "Resultados", "Reservas ordenadas de mayor a menor riesgo.")
                conteo = tabla["Nivel de riesgo"].value_counts()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Reservas evaluadas", len(tabla))
                c2.metric("🔴 Riesgo alto", int(conteo.get("Alto", 0)))
                c3.metric("🟡 Riesgo medio", int(conteo.get("Medio", 0)))
                c4.metric("🟢 Riesgo bajo", int(conteo.get("Bajo", 0)))
                columnas = ["Código de reserva", "Hotel", "Días de anticipación", "Mes de llegada",
                            "Segmento de mercado", "Tipo de depósito",
                            "Probabilidad de cancelación (%)", "Nivel de riesgo"]
                st.dataframe(tabla[columnas], width="stretch", hide_index=True,
                             column_config={"Probabilidad de cancelación (%)": st.column_config.ProgressColumn(
                                 "Probabilidad de cancelación", min_value=0, max_value=100, format="%.1f%%")})
                st.download_button("⬇️ Descargar resultados en Excel", excel_resultados(tabla),
                                   "riesgo_cancelacion_reservas.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ===============================================================
# Sección 3: Sobre el modelo
# ===============================================================
else:
    m = config["metricas_prueba"]
    with st.container(border=True):
        paso(1, "¿Qué tan bien funciona el modelo?",
             f"Resultados del modelo {config['modelo']} con reservas que no se usaron para entrenarlo.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Recall", f"{m['Recall']:.0%}")
        c1.caption("De cada 100 cancelaciones reales, el modelo detecta esta cantidad.")
        c2.metric("Precision", f"{m['Precision']:.0%}")
        c2.caption("De cada 100 alertas del modelo, esta cantidad son cancelaciones reales.")
        c3.metric("F1", f"{m['F1']:.3f}")
        c3.caption("Equilibrio entre Recall y Precision (de 0 a 1).")
        c4.metric("AUC-ROC", f"{m['AUC-ROC']:.3f}")
        c4.caption("Capacidad de distinguir reservas canceladas y no canceladas (0,5 = azar, 1 = perfecto).")

    with st.container(border=True):
        paso(2, "¿En qué se fija el modelo?",
             "Variables que más usa el modelo para separar las reservas que se cancelan de las que no.")
        nombres = [n.split("__")[1] for n in modelo.named_steps["preparacion"].get_feature_names_out()]
        importancias = pd.Series(modelo.named_steps["modelo"].feature_importances_, index=nombres)
        top = importancias.sort_values(ascending=False).head(10).sort_values()

        def nombre_columna(col):
            for variable in config["categoricas"]:
                if col.startswith(variable + "_"):
                    categoria = col[len(variable) + 1:]
                    return f"{NOMBRES_VARIABLES[variable]}: {ETIQUETAS.get(variable, {}).get(categoria, categoria)}"
            return NOMBRES_VARIABLES.get(col, col)

        grafica = go.Figure(go.Bar(x=top.values, y=[nombre_columna(c) for c in top.index], orientation="h",
                                   marker_color=AZUL, text=[f"{v:.3f}" for v in top.values],
                                   textposition="outside", cliponaxis=False))
        grafica.update_layout(height=420, margin=dict(l=10, r=50, t=10, b=40), xaxis_title="Importancia relativa")
        st.plotly_chart(grafica, width="stretch", config={"displayModeBar": False})

    with st.container(border=True):
        paso(3, "¿Cómo se interpreta el resultado?",
             "El modelo calcula una probabilidad de cancelación y la clasifica en tres niveles de riesgo.")
        columnas = st.columns(3)
        for col, (nivel, rango, prob_ejemplo) in zip(columnas, [("Bajo", "Menos de 40%", 0.1),
                                                                ("Medio", "De 40% a 70%", 0.5),
                                                                ("Alto", "70% o más", 0.9)]):
            _, color, accion = nivel_riesgo(prob_ejemplo)
            col.markdown(f"<div class='resultado' style='background:{color};padding:16px 18px'>"
                         f"<div class='nivel'>Riesgo {nivel.lower()}</div><div>{rango}</div></div>"
                         f"<p style='margin-top:8px'>{accion}</p>", unsafe_allow_html=True)

    st.caption("Modelo entrenado con reservas reales de dos hoteles en Portugal (2015–2017) siguiendo la "
               "metodología CRISP-DM. Para uso real debe reentrenarse con datos recientes del hotel.")

st.write("")
st.caption("Proyecto aplicado – Diplomado · Juan Felipe Martínez Ortega y Juan José Ariza Quintero")
