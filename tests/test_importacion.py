"""Pruebas de la importación masiva (equipos y estudiantes)."""

import io
from datetime import datetime

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models.labtrack import Equipo, Estudiante, TipoEquipo

client = TestClient(app)

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx(filas: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for f in filas:
        ws.append(f)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _subir(url: str, nombre: str, datos: bytes, **params):
    return client.post(url, files={"archivo": (nombre, datos, XLSX)}, params=params)


ENC = ["Inventario Lab", "Número de inventario", "Marca", "Modelo", "Tipo", "Estado"]


def test_importar_equipos_xlsx(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx(
        [
            ENC,
            [
                "OSC0330",
                "INV-1001",
                "Tektronix",
                "TBS1052B",
                "Osciloscopio",
                "Disponible",
            ],
            [
                "OSC0331",
                "INV-1002",
                "Keysight",
                "DSOX1102G",
                "Osciloscopio",
                "en revision",
            ],
            ["FG0001", None, "Rigol", "DG1022Z", "Generador", None],
        ]
    )
    r = _subir("/api/equipos/importar", "inv.xlsx", datos)
    assert r.status_code == 200
    body = r.json()
    assert body["aplicado"] is True
    assert body["creados"] == 3 and body["actualizados"] == 0 and body["errores"] == []

    e = db_session.execute(
        select(Equipo).where(Equipo.codigo == "OSC0331")
    ).scalar_one()
    assert e.estado == "En revisión"
    assert e.marca == "Keysight" and e.numero_inventario == "INV-1002"
    fg = db_session.execute(
        select(Equipo).where(Equipo.codigo == "FG0001")
    ).scalar_one()
    assert fg.estado == "Disponible"

    # Los campos nuevos salen en el detalle y el listado
    det = client.get("/api/equipos/OSC0330").json()
    assert det["marca"] == "Tektronix" and det["modelo"] == "TBS1052B"
    lista = {x["codigo"]: x for x in client.get("/api/equipos").json()}
    assert lista["OSC0330"]["numero_inventario"] == "INV-1001"
    app.dependency_overrides.clear()


def test_importar_equipos_es_idempotente_y_actualiza(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    base = [ENC, ["OSC0330", "INV-1001", "Tektronix", "TBS1052B", "Osciloscopio", ""]]
    _subir("/api/equipos/importar", "a.xlsx", _xlsx(base))

    nuevo = [ENC, ["OSC0330", "INV-1001", "Tektronix", "TBS1052C", "", "Baja"]]
    body = _subir("/api/equipos/importar", "a.xlsx", _xlsx(nuevo)).json()
    assert body["creados"] == 0 and body["actualizados"] == 1

    e = db_session.execute(
        select(Equipo).where(Equipo.codigo == "OSC0330")
    ).scalar_one()
    assert e.modelo == "TBS1052C" and e.estado == "Baja"
    assert e.tipo_equipo.nombre == "Osciloscopio"  # tipo vacío no lo borra
    assert len(db_session.execute(select(Equipo)).scalars().all()) == 1
    app.dependency_overrides.clear()


def test_importar_equipos_sin_tipo_usa_sin_clasificar(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx([["codigo"], ["OSC0400"]])
    assert _subir("/api/equipos/importar", "a.xlsx", datos).json()["aplicado"]
    e = db_session.execute(
        select(Equipo).where(Equipo.codigo == "OSC0400")
    ).scalar_one()
    assert e.tipo_equipo.nombre == "Sin clasificar"
    app.dependency_overrides.clear()


def test_importar_equipos_con_errores_no_guarda_nada(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx(
        [
            ENC,
            ["OSC0330", "INV-1", "A", "B", "Osciloscopio", "Disponible"],
            ["OSC0330", "INV-2", "A", "B", "Osciloscopio", "Disponible"],  # repetido
            [
                "OSC0332",
                "INV-1",
                "A",
                "B",
                "Osciloscopio",
                "Disponible",
            ],  # inv repetido
            ["OSC0333", "INV-3", "A", "B", "Osciloscopio", "Prestado"],  # estado
            [None, "INV-4", "A", "B", "Osciloscopio", ""],  # sin código
        ]
    )
    body = _subir("/api/equipos/importar", "a.xlsx", datos).json()
    assert body["aplicado"] is False
    assert [e["fila"] for e in body["errores"]] == [3, 4, 5, 6]
    assert db_session.execute(select(Equipo)).scalars().all() == []
    assert db_session.execute(select(TipoEquipo)).scalars().all() == []
    app.dependency_overrides.clear()


def test_importar_equipos_inventario_de_otro_equipo(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    _subir(
        "/api/equipos/importar",
        "a.xlsx",
        _xlsx([ENC, ["OSC1", "INV-9", "", "", "T", ""]]),
    )
    body = _subir(
        "/api/equipos/importar",
        "a.xlsx",
        _xlsx([ENC, ["OSC2", "INV-9", "", "", "T", ""]]),
    ).json()
    assert body["aplicado"] is False
    assert "OSC1" in body["errores"][0]["motivo"]
    app.dependency_overrides.clear()


def test_importar_equipo_prestado_no_cambia_estado(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    t = TipoEquipo(nombre="T")
    db_session.add(t)
    db_session.flush()
    db_session.add(Equipo(codigo="OSC1", tipo_equipo_id=t.id, estado="Prestado"))
    db_session.commit()
    body = _subir(
        "/api/equipos/importar",
        "a.xlsx",
        _xlsx([ENC, ["OSC1", "", "", "", "", "Baja"]]),
    ).json()
    assert body["aplicado"] is False and "prestado" in body["errores"][0]["motivo"]
    app.dependency_overrides.clear()


def test_dry_run_no_guarda(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx([ENC, ["OSC0330", "INV-1", "A", "B", "T", ""]])
    body = _subir("/api/equipos/importar", "a.xlsx", datos, dry_run=True).json()
    assert body["creados"] == 1 and body["aplicado"] is False and body["dry_run"]
    assert db_session.execute(select(Equipo)).scalars().all() == []
    app.dependency_overrides.clear()


def test_importar_equipos_csv_con_punto_y_coma(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    csv_txt = "codigo;marca;modelo;estado\nOSC0330;Tektronix;TBS;Disponible\n"
    r = client.post(
        "/api/equipos/importar",
        files={"archivo": ("inv.csv", csv_txt.encode("latin-1"), "text/csv")},
    )
    assert r.json()["creados"] == 1
    app.dependency_overrides.clear()


def test_archivo_invalido(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    r = client.post(
        "/api/equipos/importar", files={"archivo": ("x.txt", b"hola", "text/plain")}
    )
    assert r.status_code == 400
    r = _subir("/api/equipos/importar", "x.xlsx", b"no es excel")
    assert r.status_code == 400
    r = _subir("/api/equipos/importar", "x.xlsx", _xlsx([["marca"], ["A"]]))
    assert r.status_code == 400 and "codigo" in r.json()["detail"]
    r = _subir("/api/equipos/importar", "x.xlsx", _xlsx([]))
    assert r.status_code == 400
    app.dependency_overrides.clear()


def test_importar_estudiantes(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    db_session.add(Estudiante(nombre="Viejo Nombre", matricula="A001", uid_rfid="AB12"))
    db_session.commit()
    datos = _xlsx(
        [
            ["Matrícula", "Nombre"],
            ["A001", "Ana Torres"],
            [20210002.0, "Luis Pérez"],
        ]
    )
    body = _subir("/api/estudiantes/importar", "est.xlsx", datos).json()
    assert body["creados"] == 1 and body["actualizados"] == 1 and body["aplicado"]
    ana = db_session.execute(
        select(Estudiante).where(Estudiante.matricula == "A001")
    ).scalar_one()
    assert ana.nombre == "Ana Torres" and ana.uid_rfid == "AB12"  # RFID intacto
    assert (
        db_session.execute(select(Estudiante).where(Estudiante.matricula == "20210002"))
        .scalar_one()
        .nombre
        == "Luis Pérez"
    )
    app.dependency_overrides.clear()


def test_importar_estudiantes_errores(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx(
        [
            ["matricula", "nombre"],
            ["A1", "X"],
            ["A1", "Y"],
            ["A2", None],
            ["A3", "Z" * 200],
        ]
    )
    body = _subir("/api/estudiantes/importar", "e.xlsx", datos).json()
    assert body["aplicado"] is False
    assert [e["fila"] for e in body["errores"]] == [3, 4, 5]
    assert db_session.execute(select(Estudiante)).scalars().all() == []
    r = _subir("/api/estudiantes/importar", "e.xlsx", _xlsx([["nombre"], ["A"]]))
    assert r.status_code == 400
    app.dependency_overrides.clear()


def test_importar_formato_hoja_del_laboratorio(db_session: Session):
    """Encabezados y estados de la hoja real de inventario del lab."""
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx(
        [
            [
                "#",
                "Equipo",
                "Código lab",
                "Marca",
                "Modelo",
                "Año",
                "N° inventario",
                "Estado",
                "Observaciones",
                "Fecha",
            ],
            [
                1,
                "Osciloscopio digital",
                "OSC-0340",
                "Tektronix",
                "TDS 2022C",
                2010,
                "N00162254",
                "Sin revisar",
                None,
                None,
            ],
            [
                2,
                "Fuente de alimentación",
                "FUE1805",
                "BK Precision",
                1672,
                2009,
                438194,
                "Funciona bien",
                None,
                None,
            ],
            [None, None, None, None, None, None, None, "Sin revisar", None, None],
        ]
    )
    body = _subir("/api/equipos/importar", "inv.xlsx", datos).json()
    assert body["aplicado"] and body["total_filas"] == 2 and body["errores"] == []
    osc = db_session.execute(
        select(Equipo).where(Equipo.codigo == "OSC-0340")
    ).scalar_one()
    assert (
        osc.estado == "En revisión" and osc.tipo_equipo.nombre == "Osciloscopio digital"
    )
    fue = db_session.execute(
        select(Equipo).where(Equipo.codigo == "FUE1805")
    ).scalar_one()
    assert fue.estado == "Disponible"
    assert fue.modelo == "1672" and fue.numero_inventario == "438194"
    app.dependency_overrides.clear()


def test_observaciones_se_cargan_como_fallas_pendientes(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    enc = ["Código lab", "Marca", "Estado", "Observaciones", "Fecha"]
    fecha = datetime(2026, 10, 12)
    datos = _xlsx(
        [
            enc,
            ["OSC-1", "A", "No funciona", "NO ENCIENDE", fecha],
            ["OSC-2", "A", "Funciona bien", None, None],
        ]
    )
    body = _subir("/api/equipos/importar", "a.xlsx", datos).json()
    assert body["aplicado"] and body["fallas_creadas"] == 1

    fallas = client.get("/api/fallas", params={"estado": "Pendiente"}).json()
    assert len(fallas) == 1 and fallas[0]["descripcion"] == "NO ENCIENDE"
    assert fallas[0]["fecha"].startswith("2026-10-12")
    assert client.get("/api/equipos/OSC-2").json()["fallas"] == []

    # Repetir la carga no duplica la falla
    body = _subir("/api/equipos/importar", "a.xlsx", datos).json()
    assert body["fallas_creadas"] == 0
    assert len(client.get("/api/fallas").json()) == 1

    # Resolverla deja el equipo Disponible (flujo existente)
    r = client.patch(
        f"/api/fallas/{fallas[0]['id']}/resolver",
        json={"observacion_resolucion": "Reparado"},
    )
    assert r.status_code == 200 and r.json()["equipo_estado"] == "Disponible"
    app.dependency_overrides.clear()


def test_fecha_invalida_en_observaciones(db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    datos = _xlsx([["codigo", "observaciones", "fecha"], ["X1", "roto", "ayer"]])
    body = _subir("/api/equipos/importar", "a.xlsx", datos).json()
    assert body["aplicado"] is False and "Fecha" in body["errores"][0]["motivo"]
    app.dependency_overrides.clear()
