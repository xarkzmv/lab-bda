from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy


CONTACT_POINTS = ["127.0.0.1"]
PORTS = [9042, 9043, 9044]
KEYSPACE = "universia"

def conectar():
    for port in PORTS:
        try:
            cluster = Cluster(CONTACT_POINTS, port=port, load_balancing_policy=RoundRobinPolicy())
            session = cluster.connect(KEYSPACE)
            print(f"Conectado exitosamente al puerto {port}")
            return cluster, session
        except Exception as e:
            print(f"Puerto {port} no disponible: {e}")
    raise ConnectionError("No se pudo conectar a ningún nodo.")

def ejecutar_consultas(session):
    print("A. MATRICULADOS EN MEDICINA (ORDENADOS POR PERIODO)")
    query_a = """
        SELECT periodo, cedula, sexo, puntaje
        FROM postulantes_por_carrera
        WHERE carrera = 'MEDICINA' 
          AND matriculado = 'SI'
        ORDER BY periodo ASC
        LIMIT 10;
    """
    try:
        rows = session.execute(query_a)
        for r in rows:
            print(f"RUT: {r.cedula} | Periodo: {r.periodo} | Puntaje: {r.puntaje}")
    except Exception as e:
        print(f"Error en consulta A: {e}")

    print("B. MATRICULADOS MAULE - ING. CIVIL INFORMÁTICA")
    query_b = """
        SELECT periodo, cedula, puntaje
        FROM postulantes_por_region_carrera
        WHERE region = 'MAULE' 
          AND carrera = 'INGENIERÍA CIVIL INFORMÁTICA'
          AND matriculado = 'SI'
        ORDER BY periodo ASC
        LIMIT 10;
    """
    try:
        rows = session.execute(query_b)
        for r in rows:
            print(f"RUT: {r.cedula} | Periodo: {r.periodo}| Puntaje: {r.puntaje}")
    except Exception as e:
        print(f"Error en consulta B: {e}")


    print("C. MATRICULADOS FACULTAD CIENCIAS DE LA SALUD")
    query_c = """
        SELECT puntaje, carrera, cedula, periodo
        FROM postulantes_por_facultad
        WHERE facultad = 'CIENCIAS DE LA SALUD'
          AND matriculado = 'SI'
        ORDER BY puntaje DESC
        LIMIT 10;
    """
    try:
        rows = session.execute(query_c)
        for r in rows:
            print(f"RUT: {r.cedula}  | Carrera: {r.carrera} | Puntaje: {r.puntaje}")
    except Exception as e:
        print(f"Error en consulta C: {e}")

def main():
    cluster = None
    cluster, session = conectar()
    ejecutar_consultas(session)
    cluster.shutdown()
    print("\nConexión cerrada.")

if __name__ == '__main__':
    main()