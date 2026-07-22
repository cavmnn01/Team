import sqlite3
import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_FILE = os.environ.get("DB_PATH", "bovino_manta.db")
SAMPLE_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "expediente_bovino.json")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la estructura de tablas y carga datos de prueba con geolocalización GPS."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de animales con latitud y longitud GPS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animals (
        id TEXT PRIMARY KEY,
        qr_code TEXT UNIQUE,
        name TEXT,
        breed TEXT,
        purpose TEXT,
        hacienda TEXT,
        location TEXT,
        latitude REAL,
        longitude REAL,
        birth_date TEXT,
        weight_kg REAL,
        avg_milk_daily_liters REAL,
        current_status TEXT,
        updated_at TEXT
    )
    """)

    # Tabla de perímetros de hacienda (polígono GPS)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farm_perimeters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hacienda TEXT,
        point_order INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)

    # Tabla de vacunación
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vaccinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        animal_id TEXT,
        disease TEXT,
        date_administered TEXT,
        due_date TEXT,
        status TEXT,
        batch TEXT,
        FOREIGN KEY (animal_id) REFERENCES animals (id)
    )
    """)

    # Tabla de historial médico
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        animal_id TEXT,
        date TEXT,
        symptoms TEXT,
        diagnosis TEXT,
        treatment TEXT,
        vet_name TEXT,
        status TEXT,
        FOREIGN KEY (animal_id) REFERENCES animals (id)
    )
    """)

    # Tabla de registro diario de ordeño
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS milk_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        animal_id TEXT,
        date TEXT,
        liters REAL,
        FOREIGN KEY (animal_id) REFERENCES animals (id)
    )
    """)

    # Tabla de registro de pesaje
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        animal_id TEXT,
        date TEXT,
        weight_kg REAL,
        FOREIGN KEY (animal_id) REFERENCES animals (id)
    )
    """)

    # Tabla de Auditoría Inmutable (Ledger)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        animal_id TEXT,
        agent_source TEXT,
        action_type TEXT,
        payload_json TEXT,
        hitl_status TEXT,
        hitl_reviewer TEXT,
        hitl_comment TEXT,
        hash_sha256 TEXT,
        previous_hash TEXT
    )
    """)

    # Tabla de Usuarios RBAC
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        full_name TEXT,
        role TEXT,
        hacienda TEXT
    )
    """)

    # Usuarios por defecto
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO users (username, full_name, role, hacienda) VALUES (?, ?, ?, ?)
        """, [
            ("vaquero_sanlorenzo", "Juan Carlos Delgado", "Vaquero", "Hacienda El Encanto"),
            ("vet_manabi", "Dr. Roberto Intriago", "Veterinario", "Red Ganadera Manta"),
            ("admin_manta", "Ing. Carmen Pinchao", "Administrador", "Asociación Ganaderos Manabí")
        ])

    # Perímetro por defecto para Hacienda El Encanto (San Lorenzo, Manta)
    cursor.execute("SELECT COUNT(*) FROM farm_perimeters")
    if cursor.fetchone()[0] == 0:
        default_points = [
            ("Hacienda El Encanto", 1, -1.055, -80.905),
            ("Hacienda El Encanto", 2, -1.052, -80.892),
            ("Hacienda El Encanto", 3, -1.062, -80.888),
            ("Hacienda El Encanto", 4, -1.065, -80.901),
            ("Hacienda El Encanto", 5, -1.055, -80.905) # Cerrar polígono
        ]
        cursor.executemany("""
        INSERT INTO farm_perimeters (hacienda, point_order, latitude, longitude) VALUES (?, ?, ?, ?)
        """, default_points)

    # Animales por defecto con GPS
    cursor.execute("SELECT COUNT(*) FROM animals")
    if cursor.fetchone()[0] == 0 and os.path.exists(SAMPLE_DATA_FILE):
        with open(SAMPLE_DATA_FILE, 'r', encoding='utf-8') as f:
            sample_animals = json.load(f)

        gps_coords = [
            (-1.0580, -80.8970), # BOV-104 en San Lorenzo
            (-0.9610, -80.8120), # BOV-208 en San Mateo
            (-0.9830, -80.8410)  # BOV-312 en Santa Marianita
        ]

        for idx, animal in enumerate(sample_animals):
            lat, lon = gps_coords[idx % len(gps_coords)]
            cursor.execute("""
            INSERT INTO animals (id, qr_code, name, breed, purpose, hacienda, location, latitude, longitude, birth_date, weight_kg, avg_milk_daily_liters, current_status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                animal['id'], animal['qr_code'], animal['name'], animal['breed'],
                animal['purpose'], animal['hacienda'], animal['location'],
                lat, lon, animal['birth_date'], animal['weight_kg'],
                animal['avg_milk_daily_liters'], animal['current_status'],
                datetime.now().isoformat()
            ))

            for vac in animal.get('vaccinations', []):
                cursor.execute("""
                INSERT INTO vaccinations (animal_id, disease, date_administered, due_date, status, batch)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (animal['id'], vac['disease'], vac['date_administered'], vac['due_date'], vac['status'], vac['batch']))

            for hr in animal.get('health_history', []):
                cursor.execute("""
                INSERT INTO health_records (animal_id, date, symptoms, diagnosis, treatment, vet_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (animal['id'], hr['date'], hr['symptoms'], hr['diagnosis'], hr['treatment'], hr['vet_name'], "Completado"))

            for ml in animal.get('recent_milk_logs', []):
                cursor.execute("""
                INSERT INTO milk_logs (animal_id, date, liters)
                VALUES (?, ?, ?)
                """, (animal['id'], ml['date'], ml['liters']))

            for wl in animal.get('recent_weight_logs', []):
                cursor.execute("""
                INSERT INTO weight_logs (animal_id, date, weight_kg)
                VALUES (?, ?, ?)
                """, (animal['id'], wl['date'], wl['weight_kg']))

    conn.commit()
    conn.close()

def get_animal_by_id_or_qr(query: str) -> Optional[Dict[str, Any]]:
    """Obtiene la información completa de un bovino por ID o código QR."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM animals WHERE id = ? OR qr_code = ?", (query.upper(), query.upper()))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    animal = dict(row)

    cursor.execute("SELECT * FROM vaccinations WHERE animal_id = ?", (animal['id'],))
    animal['vaccinations'] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM health_records WHERE animal_id = ? ORDER BY date DESC", (animal['id'],))
    animal['health_history'] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT date, liters FROM milk_logs WHERE animal_id = ? ORDER BY date ASC", (animal['id'],))
    animal['recent_milk_logs'] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT date, weight_kg FROM weight_logs WHERE animal_id = ? ORDER BY date ASC", (animal['id'],))
    animal['recent_weight_logs'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return animal

def get_all_animals() -> List[Dict[str, Any]]:
    """Devuelve la lista general de bovinos registrados."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animals ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_farm_perimeter(hacienda: str = "Hacienda El Encanto") -> List[Dict[str, float]]:
    """Recupera los puntos GPS del cerco/perímetro del recinto."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude FROM farm_perimeters WHERE hacienda = ? ORDER BY point_order ASC", (hacienda,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_farm_perimeter(hacienda: str, points: List[Dict[str, float]]):
    """Actualiza los puntos de coordenadas GPS que delimitan el recinto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM farm_perimeters WHERE hacienda = ?", (hacienda,))
    for idx, p in enumerate(points):
        cursor.execute("""
        INSERT INTO farm_perimeters (hacienda, point_order, latitude, longitude)
        VALUES (?, ?, ?, ?)
        """, (hacienda, idx + 1, p["latitude"], p["longitude"]))
    conn.commit()
    conn.close()

def update_animal_gps(animal_id: str, lat: float, lon: float):
    """Actualiza la ubicación GPS en tiempo real de un animal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE animals SET latitude = ?, longitude = ?, updated_at = ? WHERE id = ?
    """, (lat, lon, datetime.now().isoformat(), animal_id))
    conn.commit()
    conn.close()

def get_last_ledger_hash() -> str:
    """Obtiene el último hash SHA-256 generado en la cadena de auditoría."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hash_sha256 FROM audit_ledger ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row and row['hash_sha256']:
        return row['hash_sha256']
    return "0000000000000000000000000000000000000000000000000000000000000000"

def add_ledger_entry(
    animal_id: str,
    agent_source: str,
    action_type: str,
    payload: Dict[str, Any],
    hitl_status: str = "PENDIENTE",
    hitl_reviewer: Optional[str] = None,
    hitl_comment: Optional[str] = None
) -> Dict[str, Any]:
    """Registra una nueva transacción inmutable en el ledger con firma SHA-256."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    previous_hash = get_last_ledger_hash()
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)

    raw_data = f"{timestamp}|{animal_id}|{agent_source}|{action_type}|{payload_str}|{hitl_status}|{previous_hash}"
    hash_sha256 = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

    cursor.execute("""
    INSERT INTO audit_ledger (timestamp, animal_id, agent_source, action_type, payload_json, hitl_status, hitl_reviewer, hitl_comment, hash_sha256, previous_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, animal_id, agent_source, action_type, payload_str,
        hitl_status, hitl_reviewer, hitl_comment, hash_sha256, previous_hash
    ))

    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": entry_id,
        "timestamp": timestamp,
        "animal_id": animal_id,
        "agent_source": agent_source,
        "action_type": action_type,
        "hitl_status": hitl_status,
        "hash_sha256": hash_sha256,
        "previous_hash": previous_hash
    }

def update_hitl_decision(entry_id: int, decision: str, reviewer: str, comment: str):
    """Actualiza la decisión del supervisor humano en un ticket existente en el Ledger."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM audit_ledger WHERE id = ?", (entry_id,))
    row = cursor.fetchone()
    if row:
        payload = json.loads(row['payload_json'])
        payload['hitl_decision_details'] = {
            "decision": decision,
            "reviewer": reviewer,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        updated_payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)

        raw_data = f"{row['timestamp']}|{row['animal_id']}|{row['agent_source']}|{row['action_type']}|{updated_payload_str}|{decision}|{row['previous_hash']}"
        new_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

        cursor.execute("""
        UPDATE audit_ledger
        SET hitl_status = ?, hitl_reviewer = ?, hitl_comment = ?, payload_json = ?, hash_sha256 = ?
        WHERE id = ?
        """, (decision, reviewer, comment, updated_payload_str, new_hash, entry_id))

        if decision == "APROBADO":
            new_status = payload.get("suggested_status", "En Tratamiento")
            cursor.execute("UPDATE animals SET current_status = ? WHERE id = ?", (new_status, row['animal_id']))

        conn.commit()
    conn.close()

def get_ledger_records(animal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Devuelve las entradas del audit ledger."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    if animal_id:
        cursor.execute("SELECT * FROM audit_ledger WHERE animal_id = ? ORDER BY id DESC", (animal_id,))
    else:
        cursor.execute("SELECT * FROM audit_ledger ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        try:
            item['payload'] = json.loads(item['payload_json'])
        except Exception:
            item['payload'] = {}
        result.append(item)
    return result

def get_user_role(username: str) -> Optional[Dict[str, str]]:
    """Obtiene el rol y permisos de un usuario."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
