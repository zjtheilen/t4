import sqlite3

gpkg_path = "experiments/graphic-spike/eldmere.gpkg"


def inspect_eldmere():
  conn = sqlite3.connect(gpkg_path)
  cursor = conn.cursor()

  print("=== EELDMERE SPATIAL INSPECTION ===")

  # 1. Fetch settlements
  cursor.execute("SELECT fid, name FROM settlements;")
  settlements = cursor.fetchall()
  print(f"\nSettlements Found ({len(settlements)}):")
  for s in settlements:
    print(f"  - ID {s[0]}: {s[1]}")

  # 2. Fetch roads count
  cursor.execute("SELECT COUNT(*) FROM roads;")
  road_count = cursor.fetchone()[0]
  print(f"\nRoad Networks Found: {road_count} feature(s)")

  conn.close()


if __name__ == "__main__":
  inspect_eldmere()