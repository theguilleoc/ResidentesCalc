import streamlit as st
import io
from datetime import datetime
import pandas as pd
import streamlit_authenticator as stauth
from dependencies import consulta_nombre,consulta_general,add_registro,crear_tabla,crear_tabla_proyectos,add_registro_proyecto,consulta_proyectos,consulta_por_codigo
from time import sleep
import json 
st.set_page_config(page_title="Libro Diario de Obra", layout="centered")

COOKIE_EXPIRY_DAYS = 30  # Días de expiración de la cookie,MANTIENE AL USUARIO LOGUEADO
# Autenticación de usuario
def main():

    try:
        consulta_general()
    except Exception:
        crear_tabla()

    db_query = consulta_general()

    registros={'usernames':{}}
    for data in db_query:
        registros['usernames'][data[1]] = {
            'name': data[0],
            'password': data[2]
        }

    authenticator = stauth.Authenticate(
        registros,
        'random_cookie_name',
        'random_signature_key',
        COOKIE_EXPIRY_DAYS,
    )
    if 'click_en_registro' not in st.session_state:
        st.session_state['click_en_registro'] = False
    if st.session_state['click_en_registro']==False:
        login_form(authenticator=authenticator)
    else:
        usuario_form()

# Garantiza existencia sin duplicar nada
crear_tabla_proyectos()
import streamlit as st
from datetime import datetime

def proceso(authenticator, name, username):
    authenticator.logout("Logout", 'main')
    st.title(f"Bienvenido {name}!")

    # Lista de actividades y roles
    actividades = [
        "Ducteado Embutido/Endosado", "Bandejado", "Cableado",
        "Montaje de Mecanismos de Iluminación", "Montaje de Artefactos",
        "MT", "Excavación", "Conexión de Tableros Eléctricos",
        "Lanzamiento de Alimentadores", "Puesta a Tierra"
    ]
    roles = ["Oficial", "Ayudante", "Contratista"]

    # 1. Encabezado
    with st.expander("1. Encabezado", expanded=True):
        c1, c2, c3 = st.columns(3)
        fecha    = c1.date_input("Fecha", datetime.today(), key="fecha")
        cliente  = c2.text_input("Cliente", key="cliente")
        proyecto = c3.text_input("Proyecto (Código)", key="proyecto")

    # 2. Condiciones Climáticas
    with st.expander("2. Condiciones Climáticas", expanded=False):
        m1, m2 = st.columns(2)
        clima_manana = m1.radio("Mañana", ["Soleado", "Nublado", "Lluvioso"], key="clima_manana", horizontal=True)
        clima_tarde  = m2.radio("Tarde",   ["Soleado", "Nublado", "Lluvioso"], key="clima_tarde",  horizontal=True)

    # 3. Actividades con rol desglosado
    st.subheader("Personal Directo")
    registro_actividades = []
    for act in actividades:
        with st.expander(act, expanded=False):
            roles_act = (["Oficial Tablerista", "Ayudante Tablerista", "Contratista"]
                         if act == "Conexión de Tableros Eléctricos" else roles)
            tabs = st.tabs(roles_act)
            datos_act = {"Actividad": act, "Roles": {}, "Obs": ""}
            for idx, role in enumerate(roles_act):
                with tabs[idx]:
                    st.markdown(f"**{role}**")
                    col1, col2 = st.columns(2)
                    cnt = col1.number_input("Personal", min_value=0, key=f"{act}_{role}_cnt")
                    hh  = col2.number_input("HH",       min_value=0.0, step=0.5, key=f"{act}_{role}_hh")
                    datos_act["Roles"][role] = {"Personal": cnt, "HH": hh}
            datos_act["Obs"] = st.text_input("Observaciones generales", key=f"{act}_obs")
            registro_actividades.append(datos_act)

    # 4. Detalle
    detalle = st.text_area("Detalle de las actividades realizadas", height=120, key="detalle")

    # 5. Equipos en obra
    st.subheader("Equipos en Obra")
    equipos = []
    for i in range(1, 4):
        e1, e2 = st.columns([3,1])
        tipo = e1.text_input(f"Tipo equipo {i}", key=f"eq_tipo_{i}")
        cant = e2.number_input("Cant.", min_value=0, key=f"eq_cant_{i}")
        equipos.append({"Tipo": tipo, "Cantidad": cant})

    # 6. Firmas
    residente  = st.text_input("Firma Residente - Nombre", key="firma_residente")
    encargado  = st.text_input("Firma Encargado - Nombre", key="firma_encargado")

    # BOTÓN DE ENVÍO (¡¡solo esto dispara el registro, no el Enter!!)
    if st.button("Confirmar registro"):
        registro = {
            "fecha":        fecha,
            "cliente":      cliente,
            "proyecto":     proyecto,
            "clima_manana": clima_manana,
            "clima_tarde":  clima_tarde,
            "detalle":      detalle,
            "actividades":  registro_actividades,
            "equipos":      equipos,
            "residente":    residente,
            "encargado":    encargado,
            "usuario":      username,
        }
        add_registro_proyecto(registro)
        st.success(f"✅ Registro para proyecto **{proyecto}** guardado en la fecha {fecha}")

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

            import json

            # Asegurarse que `actividades` sea una lista de dicts
            if isinstance(actividades, str):
                try:
                    actividades = json.loads(actividades)
                except json.JSONDecodeError:
                    st.error("El campo 'actividades' no contiene un JSON válido")
                    actividades = []

            rows = []
            
            for act in actividades:
                if isinstance(act, str):
                    try:
                        act = json.loads(act)
                    except json.JSONDecodeError:
                        st.warning("Actividad con formato inválido (no es JSON válido)")
                        continue  # saltamos este act

                if not isinstance(act, dict) or "Roles" not in act:
                    st.warning("Formato inesperado en actividad")
                    continue

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
            label="📥 Descargar Excel de planilla diaria",
            data=excel_bytes,
            file_name=f"libro_obra_{proyecto}_{fecha}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        



def generar_excel_proyecto(codigo_id: str) -> bytes:
    """
    Genera un Excel con:
    - Hoja "Resumen" → tabla con fecha, cliente, clima, residente, encargado, usuario
    - Una hoja por fecha → detalle de actividades, equipos y observaciones
    - Hoja "Totales" → sumarios agregados de HH y personal por actividad
    """
    # 1) Traer todos los registros
    registros = consulta_por_codigo(codigo_id)
    
    # 2) Preparar datos de resumen y detalle por fecha
    resumen_rows = []
    detalle_por_fecha = {}
    actividades_totales = []
    
    for (
        codigo, cliente, fecha,
        clima_manana, clima_tarde,
        detalle, actividades, equipos,
        residente, encargado, usuario
    ) in registros:
        # Fila de resumen
        resumen_rows.append({
            "Fecha": fecha,
            "Cliente": cliente,
            "Clima Mañana": clima_manana,
            "Clima Tarde": clima_tarde,
            "Residente": residente,
            "Encargado": encargado,
            "Usuario": usuario
        })
        # Guardar info diaria
        detalle_por_fecha[fecha] = {
            "detalle": detalle,
            "actividades": actividades,
            "equipos": equipos
        }
        
        # Acumular para totales (convertimos actividades JSON)
        acts = actividades
        if isinstance(acts, str):
            try:
                acts = json.loads(acts)
            except json.JSONDecodeError:
                acts = []
        if not isinstance(acts, list):
            acts = []
        for act in acts:
            if isinstance(act, str):
                try:
                    act = json.loads(act)
                except:
                    continue
            if not isinstance(act, dict) or "Roles" not in act:
                continue
            nombre = act.get("Actividad", "")
            for role, vals in act["Roles"].items():
                actividades_totales.append({
                    "Actividad": nombre,
                    "Rol": role,
                    "Personal": vals.get("Personal", 0),
                    "HH": vals.get("HH", 0)
                })
    
    df_resumen = pd.DataFrame(resumen_rows).sort_values("Fecha")
    df_totales = (
        pd.DataFrame(actividades_totales)
          .groupby("Actividad", as_index=False)
          .agg({"Personal": "sum", "HH": "sum"})
    )
    
    # 3) Escribir todo en un solo ExcelWriter
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Hoja Resumen
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
        
        # Hojas por cada fecha
        for fecha, info in detalle_por_fecha.items():
            # corregir sheet_name cuando fecha es str
            sheet_name = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
            
            # Actividades del día
            rows = []
            acts = info.get("actividades", []) or []
            if isinstance(acts, str):
                try:
                    acts = json.loads(acts)
                except:
                    acts = []
            for act in acts:
                if isinstance(act, str):
                    try:
                        act = json.loads(act)
                    except:
                        continue
                if not isinstance(act, dict) or "Roles" not in act:
                    continue
                obs = act.get("Obs", "")
                nombre = act.get("Actividad", "Sin nombre")
                for role, vals in act["Roles"].items():
                    rows.append({
                        "Actividad": nombre,
                        "Rol": role,
                        "Personal": vals.get("Personal", 0),
                        "HH": vals.get("HH", 0),
                        "Obs": obs
                    })
            df_act = pd.DataFrame(rows)
            
            # Equipos
            eqs = info.get("equipos", []) or []
            if isinstance(eqs, str):
                try:
                    eqs = json.loads(eqs)
                except:
                    eqs = []
            df_eq = pd.DataFrame(eqs)
            
            # Escribir actividades y equipos
            df_act.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
            df_eq.to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(df_act) + 2)
            
            # Detalle narrativo
            ws = writer.book[sheet_name]
            ws.cell(row=len(df_act) + len(df_eq) + 5, column=1, value="Detalle:")
            ws.cell(row=len(df_act) + len(df_eq) + 6, column=1, value=info["detalle"])
        
        # Hoja Totales
        df_totales.to_excel(writer, sheet_name="Totales", index=False)
    
    return output.getvalue()




def login_form(authenticator):
    """
    Muestra el formulario de inicio de sesión y, tras autenticar,
    da acceso a registrar o consultar por código de proyecto.
    """
    name, authentication_status, username = authenticator.login("Login")

    if authentication_status:
        st.sidebar.success(f"Sesión: {name}")
        st.title("📝 LIBRO DIARIO DE OBRA")
        menu = st.sidebar.selectbox("Menú", ["Registrar nuevo", "Consultar registros"])

        if menu == "Registrar nuevo":
            proceso(authenticator, name, username)  # tu lógica existente de guardado

        elif menu == "Consultar registros":
            st.subheader("🔍 Consultar por código de proyecto")
            
            # 1) Traer lista de códigos de proyecto
            codigos_unicos = consulta_proyectos()  # debe devolver List[str]
            
            if not codigos_unicos:
                st.warning("No hay proyectos registrados.")
                st.stop()
            
            # 2) Selector de código
            codigo_sel = st.selectbox("Seleccioná un código de proyecto:", sorted(codigos_unicos))
            
            # 3) Consultar registros para ese código
            registros = consulta_por_codigo(codigo_sel)  
            # registros: List[Tuple[11 elementos]]
            
            if not registros:
                st.warning(f"No se encontraron registros para '{codigo_sel}'.")
                st.stop()
            
            # 4) Mostrar resumen con solo Código, Cliente y Fecha
            resumen = [(r[0], r[1], r[2]) for r in registros]
            df_resumen = pd.DataFrame(resumen, columns=["Código", "Cliente", "Fecha"])
            st.dataframe(df_resumen, use_container_width=True)
            
            # 5) Selector de fecha para ver detalle
            fechas = df_resumen["Fecha"].astype(str).tolist()
            fecha_sel = st.selectbox("Ver detalle del día:", fechas)
            
            # 6) Desempaquetar y mostrar detalle completo
            idx = fechas.index(fecha_sel)
            (
                proyecto, cliente, fecha,
                clima_manana, clima_tarde,
                detalle, actividades, equipos,
                residente, encargado, usuario
            ) = registros[idx]

            st.markdown(f"### 📄 Detalle de **{codigo_sel}** — {fecha_sel}")

            # Metadatos en tres columnas
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**Cliente**\n\n{cliente}")
            m1.markdown(f"**Usuario**\n\n{usuario}")
            m2.markdown(f"**Clima Mañana**\n\n{clima_manana}")
            m2.markdown(f"**Clima Tarde**\n\n{clima_tarde}")
            m3.markdown(f"**Residente**\n\n{residente}")
            m3.markdown(f"**Encargado**\n\n{encargado}")

            # Detalle narrativo
            st.markdown("**Descripción de actividades:**")
            st.write(detalle)

            
            # Parseamos actividades si es string
            act_rows = []
            if isinstance(actividades, str):
                try:
                    actividades = json.loads(actividades)
                except json.JSONDecodeError:
                    st.error("❌ El campo 'actividades' no es un JSON válido")
                    actividades = []

            # Validamos que sea lista
            if not isinstance(actividades, list):
                st.error("⚠️ 'actividades' no es una lista válida")
                actividades = []

            # Recorremos actividades
            for i, act in enumerate(actividades):
                if isinstance(act, str):
                    try:
                        act = json.loads(act)
                    except json.JSONDecodeError:
                        st.warning(f"⛔ Actividad [{i}] no es JSON válido")
                        continue

                if not isinstance(act, dict) or "Roles" not in act:
                    st.warning(f"⚠️ Actividad [{i}] no tiene estructura esperada")
                    continue

                for role, vals in act["Roles"].items():
                    act_rows.append({
                        "Actividad": act.get("Actividad", ""),
                        "Rol":        role,
                        "Personal":   vals.get("Personal", 0),
                        "HH":         vals.get("HH", 0),
                        "Obs":        act.get("Obs", "")
                    })

            df_act = pd.DataFrame(act_rows)
            st.markdown("**🔧 Actividades por rol**")
            st.table(df_act)

            # --- EQUIPOS ---

            # Parseamos si viene como string
            if isinstance(equipos, str):
                try:
                    equipos = json.loads(equipos)
                    
                except json.JSONDecodeError:
                    st.error("❌ El campo 'equipos' no es un JSON válido")
                    equipos = []

            # Validamos que sea lista
            if not isinstance(equipos, list):
                st.error("⚠️ 'equipos' no es una lista válida")
                equipos = []

            df_eq = pd.DataFrame(equipos)
            st.markdown("**🚜 Equipos en obra**")
            st.table(df_eq)
            
            excel_bytes = generar_excel_proyecto(codigo_sel)

            # Y mostramos un único botón de descarga
            st.download_button(
                label="📥 Descargar REPORTE COMPLETO",
                data=excel_bytes,
                file_name=f"{codigo_sel}_resumen_{datetime.today().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        st.markdown(
                    "<div style='text-align: right; color: gray; font-size: 0.9em;'>Developed by Guillermo Ojeda Cueto</div>",
                    unsafe_allow_html=True
                )

    elif authentication_status is False:
        st.error("Usuario o contraseña incorrectos.")
    else:  # authentication_status is None
        st.warning("Por favor, ingresa tus credenciales.")
        if st.button("Registrarse"):
            st.session_state['click_en_registro'] = True
            st.rerun()


def confirm_msg():
    """Intenta crear el usuario. 
       Devuelve True si se agregó, False en caso contrario."""
    # 1) Verifico contraseñas
    if st.session_state['password'] != st.session_state['confirmar_password']:
        st.error("🔒 Las contraseñas no coinciden.")
        sleep(3)
        return False

    # 2) Verifico existencia previa
    if consulta_nombre(st.session_state['usuario']):
        st.warning("❗ El usuario ya existe.")
        sleep(3)
        return False

    # 3) Si todo OK, hago el registro
    hashed = stauth.Hasher([st.session_state['password']]).generate()[0]
    add_registro(
        st.session_state['nombre'].strip(),
        st.session_state['usuario'].strip(),
        hashed
    )
    st.success("✅ Usuario registrado correctamente.")
    sleep(3)
    return True


def usuario_form():
    with st.form(key='formulario', clear_on_submit=True):
        st.text_input("Nombre", key="nombre")
        st.text_input("Usuario", key="usuario")
        st.text_input("Contraseña",     type="password", key="password")
        st.text_input("Confirmar contraseña", type="password", key="confirmar_password")
        registrar = st.form_submit_button("Registrar")

    if registrar:
        # Validación de campos vacíos
        campos = [st.session_state['nombre'],
                  st.session_state['usuario'],
                  st.session_state['password'],
                  st.session_state['confirmar_password']]
        if not all(c.strip() for c in campos):
            st.error("❗ Por favor completa todos los campos antes de registrar.")
            return  # corto antes de llamar a confirm_msg()

        # Llamo a confirm_msg() y, si retorna True, puedo hacer otras cosas (o nada más)
        if confirm_msg():
            # aquí podrías redirigir, limpiar el estado, etc.
            pass

    # Botón para volver al login
    if st.button("Volver al Login"):
        st.session_state['click_en_registro'] = False
        st.rerun()

if __name__ == "__main__":
    main()
