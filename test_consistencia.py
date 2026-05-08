from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("universia")


query = SimpleStatement(
    """
    SELECT *
    FROM postulantes_por_carrera
    WHERE carrera = 'MEDICINA'
      AND matriculado = 'SI'
    LIMIT 5
    """,
    consistency_level=ConsistencyLevel.THREE
)

try:
    rows = session.execute(query)

    print("Query funcionó con consistencia THREE")

    for r in rows:
            print(f"RUT: {r.cedula} ")

except Exception as e:
    print("\n Query falló:")
    print(e)

cluster.shutdown()