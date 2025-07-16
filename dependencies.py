# dependencies.py

import os
import json
from datetime import date
from dotenv import load_dotenv
from supabase import create_client

# 1) Carga variables de entorno
load_dotenv()

# 2) Credenciales Supabase
AUTH_URL = os.getenv("AUTH_URL")
AUTH_KEY = os.getenv("AUTH_KEY")
PROY_URL = os.getenv("PROY_URL")
PROY_KEY = os.getenv("PROY_KEY")

# 3) Inicializar clientes
auth_db = create_client(AUTH_URL, AUTH_KEY)
proy_db = create_client(PROY_URL, PROY_KEY)

# 4) Función auxiliar para JSON
def to_json(field):
    if isinstance(field, str):
        try:
            json.loads(field)
            return field
        except json.JSONDecodeError:
            return json.dumps([], ensure_ascii=False)
    return json.dumps(field, ensure_ascii=False)

# ============================
# 🔐 SECCIÓN: USUARIOS
# ============================

def crear_tabla():
    print("🛠️  Crea la tabla 'registros' en tu proyecto auth_table vía SQL Editor.")

def add_registro(nombre, usuario, password):
    auth_db.table("registros") \
           .insert({"nombre": nombre, "usuario": usuario, "password": password}) \
           .execute()

def consulta_general():
    """
    Devuelve una lista de tuplas (nombre, usuario, password),
    tal como tu código espera (r[0], r[1], r[2]).
    """
    res = auth_db.table("registros") \
                 .select("nombre", "usuario", "password") \
                 .execute()
    # res.data es una lista de dicts; la convertimos a tuplas
    return [(r["nombre"], r["usuario"], r["password"]) for r in res.data]

def consulta_nombre(user):
    res = auth_db.table("registros") \
                 .select("nombre", "usuario", "password") \
                 .eq("usuario", user) \
                 .execute()
    return [(r["nombre"], r["usuario"], r["password"]) for r in res.data]


# ============================
# 🏗️ SECCIÓN: PROYECTOS
# ============================

def crear_tabla_proyectos():
    print("🛠️  Crea las tablas 'proyectos' y 'registros' en tu proyecto proyectos vía SQL Editor.")

def add_registro_proyecto(registro: dict):
    # 1) Upsert proyecto meta
    proy_db.table("proyectos") \
          .upsert({
              "codigo_id": registro["proyecto"],
              "cliente":    registro["cliente"]
          }, on_conflict="codigo_id") \
          .execute()

    # 2) Obtener id interno
    resp = proy_db.table("proyectos") \
                 .select("id") \
                 .eq("codigo_id", registro["proyecto"]) \
                 .single() \
                 .execute()
    proyecto_id = resp.data["id"]

    # 3) Serializar fecha
    raw_fecha = registro["fecha"]
    fecha_str = raw_fecha.isoformat() if isinstance(raw_fecha, date) else raw_fecha

    # 4) Upsert registro diario
    data = {
        "proyecto_id":  proyecto_id,
        "fecha":        fecha_str,
        "clima_manana": registro.get("clima_manana"),
        "clima_tarde":  registro.get("clima_tarde"),
        "detalle":      registro["detalle"],
        "actividades":  to_json(registro["actividades"]),
        "equipos":      to_json(registro["equipos"]),
        "residente":    registro["residente"],
        "encargado":    registro["encargado"],
        "usuario":      registro["usuario"],
    }

    proy_db.table("registros") \
          .upsert(data, on_conflict="proyecto_id,fecha") \
          .execute()

def consulta_proyectos():
    res = proy_db.table("proyectos") \
                 .select("codigo_id") \
                 .execute()
    codes = [r["codigo_id"] for r in res.data]
    return sorted(set(codes))

def consulta_por_codigo(codigo_id: str):
    # 1) Obtener cliente
    resp_cli = proy_db.table("proyectos") \
                     .select("cliente") \
                     .eq("codigo_id", codigo_id) \
                     .single() \
                     .execute()
    cliente = resp_cli.data["cliente"]

    # 2) Obtener id interno
    resp_id = proy_db.table("proyectos") \
                    .select("id") \
                    .eq("codigo_id", codigo_id) \
                    .single() \
                    .execute()
    proyecto_id = resp_id.data["id"]

    # 3) Traer registros ordenados
    res = proy_db.table("registros") \
                 .select("*") \
                 .eq("proyecto_id", proyecto_id) \
                 .order("fecha") \
                 .execute()

    # 4) Convertir a tuplas de 11 elementos:
    tuples = []
    for r in res.data:
        tuples.append((
            codigo_id,
            cliente,
            r["fecha"],
            r.get("clima_manana"),
            r.get("clima_tarde"),
            r.get("detalle", ""),
            r.get("actividades", []),
            r.get("equipos", []),
            r.get("residente", ""),
            r.get("encargado", ""),
            r.get("usuario", ""),
        ))
    return tuples
