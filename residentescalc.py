import os
import io
from datetime import date as dt_date
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Libro Diario de Obra", layout="wide")
st.title("📝 LIBRO DIARIO DE OBRA")

# Lista de actividades a registrar
actividades = [
    "Ducteado Embutido/Endosado", "Bandejado", "Cableado",
    "Montaje de Mecanismos de Iluminación", "Montaje de Artefactos",
    "MT", "Excavación", "Conexión de Tableros Eléctricos",
    "Lanzamiento de Alimentadores", "Puesta a Tierra"
]

# Formulario principal
with st.form(key="form_registro"):
    # 1. Encabezado
    with st.expander("1. Encabezado", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha = st.date_input("Fecha", dt_date.today(), key="fecha")
        with c2:
            cliente = st.text_input("Cliente", key="cliente")
        with c3:
            proyecto = st.text_input("Proyecto (Código)", key="proyecto")

    # 2. Condiciones Climáticas
    with st.expander("2. Condiciones Climáticas", expanded=False):
        m1, m2 = st.columns(2)
        with m1:
            clima_manana = st.radio(
                "Mañana", ["Soleado", "Nublado", "Lluvioso"],
                horizontal=True, key="clima_manana"
            )
        with m2:
            clima_tarde = st.radio(
                "Tarde", ["Soleado", "Nublado", "Lluvioso"],
                horizontal=True, key="clima_tarde"
            )

    # 3. Actividades\ n    st.subheader("3. Personal Directo y Cantidad Instalada")
    registro_actividades = []
    for act in actividades:
        with st.expander(act):
            p1, p2, p3 = st.columns([1,1,2])
            cnt = p1.number_input("Personal", min_value=0, key=f"cnt_{act}")
            hh  = p2.number_input("HH", min_value=0.0, step=0.5, key=f"hh_{act}")
            obs = p3.text_input("Obs", key=f"obs_{act}")
            registro_actividades.append({"Actividad": act, "Personal": cnt, "HH": hh, "Obs": obs})

    # 4. Detalle de actividades
    detalle = st.text_area(
        "4. Detalle de las actividades realizadas", height=120, key="detalle"
    )

    # 5. Equipos en obra
    st.subheader("5. Equipos en Obra")
    equipos = []
    for i in range(1, 4):
        e1, e2 = st.columns([3,1])
        tipo = e1.text_input(f"Tipo equipo {i}", key=f"eq_tipo_{i}")
        cant = e2.number_input("Cant.", min_value=0, key=f"eq_cant_{i}")
        equipos.append({"Tipo": tipo, "Cantidad": cant})

    # 6. Firmas y envío
    residente = st.text_input("Firma Residente - Nombre", key="firma_residente")
    encargado = st.text_input("Firma Encargado - Nombre", key="firma_encargado")

    # Botón de envío dentro del form
    enviar = st.form_submit_button(
        label="Enviar formulario",
        use_container_width=True
    )

# Función para generar Excel
def generar_excel(fecha, cliente, proyecto, clima_manana, clima_tarde, actividades, detalle, equipos):
    # Crear DataFrames
    df_encabezado = pd.DataFrame({
        "Fecha": [fecha],
        "Cliente": [cliente],
        "Proyecto": [proyecto],
        "Clima Mañana": [clima_manana],
        "Clima Tarde": [clima_tarde]
    })
    df_act = pd.DataFrame(actividades)
    df_detalle = pd.DataFrame({"Detalle": [detalle]})
    df_eq = pd.DataFrame(equipos)

    # Escribir a Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_encabezado.to_excel(writer, sheet_name="Encabezado", index=False)
        df_act.to_excel(writer, sheet_name="Actividades", index=False)
        df_detalle.to_excel(writer, sheet_name="Detalle", index=False)
        df_eq.to_excel(writer, sheet_name="Equipos", index=False)
    return output.getvalue()

# Mostrar resultado y gráficos, luego descarga
if enviar:
    st.success("¡Formulario enviado correctamente!")
    # Mostrar datos ingresados
    st.json({
        "fecha": str(fecha),
        "cliente": cliente,
        "proyecto": proyecto,
        "clima_mañana": clima_manana,
        "clima_tarde": clima_tarde,
        "detalle": detalle
    })

    import plotly.express as px
    import plotly.graph_objects as go

    # DataFrames para gráficos
    df_actividades = pd.DataFrame(registro_actividades)

    # Gráfico 1: Horas Hombre por Actividad (Barra interactiva)
    fig_hh = px.bar(
        df_actividades,
        x="Actividad",
        y="HH",
        text="HH",
        title="Horas Hombre por Actividad",
        labels={"HH": "Horas Hombre"},
        color="HH",
        color_continuous_scale="Blues"
    )
    fig_hh.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_hh, use_container_width=True)

    # Gráfico 2: Personal por Actividad (Barra interactiva)
    fig_personal = px.bar(
        df_actividades,
        x="Actividad",
        y="Personal",
        text="Personal",
        title="Personal en Obra por Actividad",
        labels={"Personal": "Nº Personal"},
        color="Personal",
        color_continuous_scale="Greens"
    )
    fig_personal.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_personal, use_container_width=True)

    # Gráfico 3: Pie chart de distribución de HH (sin actividades con 0%)
    df_pie = df_actividades[df_actividades["HH"] > 0]
    fig_pie = px.pie(
        df_pie,
        names="Actividad",
        values="HH",
        title="Distribución de Horas Hombre por Actividad",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    

    # Botón de descarga Excel
    excel_bytes = generar_excel(
        fecha, cliente, proyecto,
        clima_manana, clima_tarde,
        registro_actividades, detalle, equipos
    )
    st.download_button(
        label="📥 Descargar Excel",
        data=excel_bytes,
        file_name=f"libro_obra_{proyecto}_{fecha}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
