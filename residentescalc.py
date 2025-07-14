import io
from datetime import date as dt_date
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Libro Diario de Obra", layout="wide")
st.title("📝 LIBRO DIARIO DE OBRA")

# Lista de actividades y roles
actividades = [
    "Ducteado Embutido/Endosado", "Bandejado", "Cableado",
    "Montaje de Mecanismos de Iluminación", "Montaje de Artefactos",
    "MT", "Excavación", "Conexión de Tableros Eléctricos",
    "Lanzamiento de Alimentadores", "Puesta a Tierra"
]
roles = ["Oficial", "Ayudante", "Contratista"]

# Formulario principal
with st.form(key="form_registro"):
    # 1. Encabezado
    with st.expander("1. Encabezado", expanded=True):
        c1, c2, c3 = st.columns(3)
        fecha = c1.date_input("Fecha", dt_date.today(), key="fecha")
        cliente = c2.text_input("Cliente", key="cliente")
        proyecto = c3.text_input("Proyecto (Código)", key="proyecto")

    # 2. Condiciones Climáticas
    with st.expander("2. Condiciones Climáticas", expanded=False):
        m1, m2 = st.columns(2)
        clima_manana = m1.radio("Mañana", ["Soleado", "Nublado", "Lluvioso"], key="clima_manana", horizontal=True)
        clima_tarde = m2.radio("Tarde", ["Soleado", "Nublado", "Lluvioso"], key="clima_tarde", horizontal=True)

    # 3. Actividades con rol desglosado
    st.subheader("Personal Directo")
    registro_actividades = []
    for act in actividades:
        # Usar expander para cada actividad
        with st.expander(f"{act}", expanded=False):
            # Definir roles especiales para "Conexión de Tableros Eléctricos"
            if act == "Conexión de Tableros Eléctricos":
                roles_act = ["Oficial Tablerista", "Ayudante Tablerista", "Contratista"]
            else:
                roles_act = roles
            # Usamos pestañas para cada rol para una interfaz más limpia
            tabs = st.tabs(roles_act)
            datos_act = {"Actividad": act, "Roles": {}, "Obs": ""}
            for idx, role in enumerate(roles_act):
                with tabs[idx]:
                    st.markdown(f"**{role}**")
                    col1, col2 = st.columns(2)
                    cant = col1.number_input(f"Personal", min_value=0, key=f"{act}_{role}_cnt")
                    hh   = col2.number_input(f"HH", min_value=0.0, step=0.5, key=f"{act}_{role}_hh")
                    datos_act["Roles"][role] = {"Personal": cant, "HH": hh}
            # Campo de observaciones al final
            obs = st.text_input("Observaciones generales", key=f"{act}_obs")
            datos_act["Obs"] = obs
            registro_actividades.append(datos_act)
    detalle = st.text_area("4. Detalle de las actividades realizadas", height=120, key="detalle")

    # 5. Equipos en obra
    st.subheader("Equipos en Obra")
    equipos = []
    for i in range(1, 4):
        e1, e2 = st.columns([3,1])
        tipo = e1.text_input(f"Tipo equipo {i}", key=f"eq_tipo_{i}")
        cant = e2.number_input("Cant.", min_value=0, key=f"eq_cant_{i}")
        equipos.append({"Tipo": tipo, "Cantidad": cant})

    # 6. Firmas
    residente = st.text_input("Firma Residente - Nombre", key="firma_residente")
    encargado = st.text_input("Firma Encargado - Nombre", key="firma_encargado")

    # Submit button
    submitted = st.form_submit_button("Confirmar registro")

# Función para generar Excel
def generar_excel(fecha, cliente, proyecto, clima_manana, clima_tarde, actividades, detalle, equipos):
    # Encabezado
    df_enc = pd.DataFrame({
        "Fecha": [fecha],
        "Cliente": [cliente],
        "Proyecto": [proyecto],
        "Clima Mañana": [clima_manana],
        "Clima Tarde": [clima_tarde],
        "Residente": [residente],
        "Encargado": [encargado]
    })
    # Actividades por rol
    rows = []
    for act in actividades:
        for role, vals in act["Roles"].items():
            rows.append({
                "Actividad": act["Actividad"],
                "Rol": role,
                "Personal": vals["Personal"],
                "HH": vals["HH"],
                "Obs": act.get("Obs", "")
            })
    df_act = pd.DataFrame(rows)
    df_det = pd.DataFrame({"Detalle": [detalle]})
    df_eq = pd.DataFrame(equipos)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_enc.to_excel(writer, sheet_name="Encabezado", index=False)
        df_act.to_excel(writer, sheet_name="Actividades", index=False)
        df_det.to_excel(writer, sheet_name="Detalle", index=False)
        df_eq.to_excel(writer, sheet_name="Equipos", index=False)
    return output.getvalue()

# Mostrar resultados, gráficos y descarga
import plotly.graph_objects as go

# Gráficos: totales por actividad
hh_sum = [sum([v["HH"] for v in act["Roles"].values()]) for act in registro_actividades]
p_sum  = [sum([v["Personal"] for v in act["Roles"].values()]) for act in registro_actividades]
labels = [act["Actividad"] for act in registro_actividades]

# Gráfico interactivo de Horas Hombre por Actividad
fig1 = go.Figure(data=[
    go.Bar(x=labels, y=hh_sum, marker_color='indigo')
])
fig1.update_layout(
    title="Total Horas Hombre por Actividad",
    xaxis_title="Actividad",
    yaxis_title="Horas Hombre",
    xaxis_tickangle=-45
)
st.plotly_chart(fig1, use_container_width=True)

# Gráfico interactivo de Personal por Actividad
fig2 = go.Figure(data=[
    go.Bar(x=labels, y=p_sum, marker_color='teal')
])
fig2.update_layout(
    title="Total Personal por Actividad",
    xaxis_title="Actividad",
    yaxis_title="Personal",
    xaxis_tickangle=-45
)
st.plotly_chart(fig2, use_container_width=True)

# Descargar Excel
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
st.markdown(
    "<div style='text-align: right; color: gray; font-size: 0.9em;'>Developed by Guillermo Ojeda Cueto</div>",
    unsafe_allow_html=True
)
