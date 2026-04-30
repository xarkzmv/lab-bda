"""
poblar_cassandra.py
────────────────────────────────────────────────────────────────
Carga el archivo postulaciones.xlsx en las 3 tablas de Cassandra.

Uso:
    pip install cassandra-driver pandas openpyxl
    python poblar_cassandra.py

El docker-compose expone:
    nodo_1 → localhost:7001
    nodo_2 → localhost:7002
    nodo_3 → localhost:7003
────────────────────────────────────────────────────────────────
"""

import math
import time
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from cassandra import ConsistencyLevel
from cassandra.query import BatchStatement, SimpleStatement

# ──────────────────────────────────────────────
# CONFIGURACIÓN — ajusta si cambiaste los puertos
# ──────────────────────────────────────────────
EXCEL_PATH   = "postulaciones.xlsx"   # ruta al archivo Excel
CONTACT_POINTS = ["127.0.0.1"]        # IP del host Docker
PORTS        = [9042, 9043, 9044]     # puertos del docker-compose actual
KEYSPACE     = "universia"
BATCH_SIZE   = 50                     # filas por batch (no superar 100 en Cassandra)

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def safe_float(val):
    """Convierte a float; devuelve None si es NaN o vacío."""
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None

def safe_int(val):
    """Convierte a int; devuelve None si es NaN o vacío."""
    try:
        f = float(val)
        return None if math.isnan(f) else int(f)
    except (TypeError, ValueError):
        return None

def safe_str(val):
    """Convierte a str en mayúsculas; devuelve None si está vacío."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip().upper()
    return s if s else None

# ──────────────────────────────────────────────
# CONEXIÓN
# ──────────────────────────────────────────────

def conectar():
    """Intenta conectar a cualquiera de los 3 nodos."""
    for port in PORTS:
        try:
            cluster = Cluster(
                CONTACT_POINTS,
                port=port,
                load_balancing_policy=RoundRobinPolicy(),
                connect_timeout=10,
            )
            session = cluster.connect(KEYSPACE)
            print(f"✅ Conectado a Cassandra en puerto {port}")
            return cluster, session
        except Exception as e:
            print(f"⚠️  Puerto {port} no disponible: {e}")
    raise ConnectionError("❌ No se pudo conectar a ningún nodo de Cassandra.")

# ──────────────────────────────────────────────
# PREPARED STATEMENTS
# ──────────────────────────────────────────────

def preparar_statements(session):
    """Prepara los INSERT para las 3 tablas."""

    # NOTA: las tablas usan (carrera, estado) + periodo como PK.
    # Para evitar sobreescribir filas con mismo periodo, añadimos
    # cedula como parte del valor — Cassandra guarda la última escritura
    # (last-write-wins). Si quieres unicidad real, hay que recrear
    # las tablas con cedula en la clustering key.

    stmt_carrera = session.prepare("""
        INSERT INTO postulantes_por_carrera
            (carrera, estado, periodo, cedula, sexo, preferencia,
             facultad, puntaje, grupo_depen, region,
             latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    stmt_region = session.prepare("""
        INSERT INTO postulantes_por_region_carrera
            (region, carrera, estado, periodo, cedula, sexo, preferencia,
             facultad, puntaje, grupo_depen,
             latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    stmt_facultad = session.prepare("""
        INSERT INTO postulantes_por_facultad
            (facultad, estado, puntaje, cedula, periodo, sexo, preferencia,
             carrera, grupo_depen, region,
             latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    return stmt_carrera, stmt_region, stmt_facultad

# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────

def cargar_datos(session, df, stmt_carrera, stmt_region, stmt_facultad):
    total = len(df)
    errores = 0

    batch_c = BatchStatement(consistency_level=ConsistencyLevel.ONE)
    batch_r = BatchStatement(consistency_level=ConsistencyLevel.ONE)
    batch_f = BatchStatement(consistency_level=ConsistencyLevel.ONE)
    count_c = count_r = count_f = 0

    def flush_batch(batch, nombre):
        try:
            session.execute(batch)
        except Exception as e:
            print(f"  ⚠️  Error en batch {nombre}: {e}")

    for i, row in df.iterrows():
        try:
            # ── Valores comunes ──────────────────────────────
            carrera     = safe_str(row.get("CARRERA"))
            estado      = safe_str(row.get("MATRICULADO") or row.get("ESTADO"))
            periodo     = safe_int(row.get("PERIODO"))
            cedula      = safe_str(row.get("CEDULA"))
            sexo        = safe_str(row.get("SEXO"))
            preferencia = safe_int(row.get("PREFERENCIA"))
            facultad    = safe_str(row.get("FACULTAD"))
            puntaje     = safe_float(row.get("PUNTAJE"))
            grupo_depen = safe_str(row.get("GRUPO_DEPEN"))
            region      = safe_str(row.get("REGION"))
            latitud     = safe_float(row.get("LATITUD"))
            longitud    = safe_float(row.get("LONGITUD"))
            ptje_nem    = safe_float(row.get("PTJE_NEM"))
            psu_promlm  = safe_float(row.get("PSU_PROMLM"))
            pace        = safe_str(row.get("PACE"))
            gratuidad   = safe_str(row.get("GRATUIDAD"))

            # ── Tabla 1: postulantes_por_carrera ─────────────
            batch_c.add(stmt_carrera, (
                carrera, estado, periodo, cedula, sexo, preferencia,
                facultad, puntaje, grupo_depen, region,
                latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad
            ))
            count_c += 1

            # ── Tabla 2: postulantes_por_region_carrera ──────
            batch_r.add(stmt_region, (
                region, carrera, estado, periodo, cedula, sexo, preferencia,
                facultad, puntaje, grupo_depen,
                latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad
            ))
            count_r += 1

            # ── Tabla 3: postulantes_por_facultad ────────────
            # puntaje puede ser None; Cassandra no acepta None en clustering key
            puntaje_safe = puntaje if puntaje is not None else 0.0
            batch_f.add(stmt_facultad, (
                facultad, estado, puntaje_safe, cedula, periodo, sexo, preferencia,
                carrera, grupo_depen, region,
                latitud, longitud, ptje_nem, psu_promlm, pace, gratuidad
            ))
            count_f += 1

        except Exception as e:
            errores += 1
            print(f"  ⚠️  Fila {i} omitida: {e}")

        # ── Enviar batch cada BATCH_SIZE filas ───────────────
        if count_c >= BATCH_SIZE:
            flush_batch(batch_c, "postulantes_por_carrera")
            batch_c = BatchStatement(consistency_level=ConsistencyLevel.ONE)
            count_c = 0

        if count_r >= BATCH_SIZE:
            flush_batch(batch_r, "postulantes_por_region_carrera")
            batch_r = BatchStatement(consistency_level=ConsistencyLevel.ONE)
            count_r = 0

        if count_f >= BATCH_SIZE:
            flush_batch(batch_f, "postulantes_por_facultad")
            batch_f = BatchStatement(consistency_level=ConsistencyLevel.ONE)
            count_f = 0

        # ── Progreso cada 500 filas ───────────────────────────
        if (i + 1) % 500 == 0:
            print(f"  → {i + 1}/{total} filas procesadas...")

    # ── Flush final de lo que quedó en los batches ────────────
    if count_c > 0: flush_batch(batch_c, "postulantes_por_carrera")
    if count_r > 0: flush_batch(batch_r, "postulantes_por_region_carrera")
    if count_f > 0: flush_batch(batch_f, "postulantes_por_facultad")

    return errores

# ──────────────────────────────────────────────
# VERIFICACIÓN
# ──────────────────────────────────────────────

def verificar(session):
    print("\n📊 Verificando conteo de filas en cada tabla:")
    tablas = [
        "postulantes_por_carrera",
        "postulantes_por_region_carrera",
        "postulantes_por_facultad",
    ]
    for tabla in tablas:
        try:
            # COUNT(*) es lento en Cassandra pero útil para verificar
            r = session.execute(f"SELECT COUNT(*) FROM {tabla}")
            print(f"  {tabla}: {r.one()[0]:,} filas")
        except Exception as e:
            print(f"  {tabla}: error al contar — {e}")

    print("\n🔍 Prueba de las 3 consultas del negocio:")

    print("\n  a) Matriculados en MEDICINA:")
    rows = session.execute("""
        SELECT cedula, periodo, sexo, puntaje
        FROM postulantes_por_carrera
        WHERE carrera = 'MEDICINA' AND estado = 'MATRICULADO'
        LIMIT 5
    """)
    for r in rows:
        print(f"     {r}")

    print("\n  b) Matriculados del Maule en ING. CIVIL INFORMATICA:")
    rows = session.execute("""
        SELECT cedula, periodo, sexo, puntaje
        FROM postulantes_por_region_carrera
        WHERE region  = 'REGION DEL MAULE'
          AND carrera = 'INGENIERIA CIVIL INFORMATICA'
          AND estado  = 'MATRICULADO'
        LIMIT 5
    """)
    for r in rows:
        print(f"     {r}")

    print("\n  c) Matriculados en CIENCIAS DE LA SALUD (top puntaje):")
    rows = session.execute("""
        SELECT cedula, puntaje, carrera, periodo
        FROM postulantes_por_facultad
        WHERE facultad = 'CIENCIAS DE LA SALUD'
          AND estado   = 'MATRICULADO'
        LIMIT 5
    """)
    for r in rows:
        print(f"     {r}")

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Cargador de datos → Cassandra UniversiaCluster")
    print("=" * 55)

    # 1. Leer Excel
    print(f"\n📂 Leyendo {EXCEL_PATH}...")
    try:
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo '{EXCEL_PATH}'.")
        print("   Colócalo en la misma carpeta que este script.")
        return

    # Normalizar nombres de columnas a mayúsculas
    df.columns = [c.strip().upper() for c in df.columns]
    print(f"   {len(df):,} filas | columnas: {list(df.columns)}")

    # Normalizar columna ESTADO (puede llamarse MATRICULADO en el Excel)
    if "MATRICULADO" in df.columns and "ESTADO" not in df.columns:
        df["ESTADO"] = df["MATRICULADO"]

    # 2. Conectar
    print("\n🔌 Conectando a Cassandra...")
    cluster, session = conectar()

    # 3. Preparar statements
    stmt_c, stmt_r, stmt_f = preparar_statements(session)

    # 4. Cargar
    print(f"\n⬆️  Cargando {len(df):,} filas en 3 tablas (batch={BATCH_SIZE})...")
    inicio = time.time()
    errores = cargar_datos(session, df, stmt_c, stmt_r, stmt_f)
    elapsed = time.time() - inicio

    print(f"\n✅ Carga completada en {elapsed:.1f}s | errores: {errores}")

    # 5. Verificar
    verificar(session)

    # 6. Cerrar
    cluster.shutdown()
    print("\n🔒 Conexión cerrada.")

if __name__ == "__main__":
    main()