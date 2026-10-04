from fastapi import FastAPI, HTTPException
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from shapely.geometry import LineString
from geoalchemy2 import WKTElement
from sqlalchemy import text

import gpxpy
import json
import uuid

from sqlalchemy import text

from app.db import engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_gpx(file: UploadFile):

    activity_id = str(uuid.uuid4())

    content = await file.read()
    gpx = gpxpy.parse(content.decode())

    coords = []
    times = []

    # ① まず全部集める
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.latitude and point.longitude:
                    coords.append((point.longitude, point.latitude))
                    if point.time:
                        times.append(point.time)

    # データチェック
    if not coords:
        return {"error": "no points"}

    # 位置情報日記など、ほぼ移動がなく1点しか記録されない場合にも
    # LineStringを作成できるよう、同一点を複製する（距離0の記録になる）
    if len(coords) == 1:
        coords.append(coords[0])
    if len(times) == 1:
        times.append(times[0])

    # ② LINESTRING作成（ここで1回だけ）
    line = LineString(coords)

    with engine.begin() as conn:

        conn.execute(
            text("""
            INSERT INTO activities(
                id,
                start_time,
                end_time,
                distance,
                avg_speed,
                path
            )
            VALUES(
                :id,
                :start_time,
                :end_time,
                ST_Length(ST_GeomFromText(:path, 4326)::geography),
                (
                    ST_Length(ST_GeomFromText(:path, 4326)::geography)
                    / NULLIF(EXTRACT(EPOCH FROM (:end_time - :start_time)), 0)
                ) * 3.6,
                ST_GeomFromText(:path, 4326)
            )
            """),
            {
                "id": activity_id,
                "start_time": min(times),
                "end_time": max(times),
                "path": line.wkt
            }
        )
    return {
        "activity_id": activity_id
    }

@app.get("/get/{activity_id}")
def get_activity(activity_id: str):

    with engine.begin() as conn:

        result = conn.execute(
            text("""
            SELECT
                ST_AsGeoJSON(path) as geojson,
                start_time,
                end_time
            FROM activities
            WHERE id = :id
            """),
            {"id": activity_id}
        ).first()

    return {
        "activity_id": activity_id,
        "geojson": json.loads(result.geojson),
        "start_time": result.start_time,
        "end_time": result.end_time
    }

@app.get("/activities")
def list_activities():

    with engine.begin() as conn:

        result = conn.execute(
            text("""
            SELECT
                id,
                start_time,
                end_time,
                distance,
                avg_speed
            FROM activities
            ORDER BY start_time DESC
            """)
        )

        activities = []
        for row in result:
            activities.append({
                "id": row.id,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "distance": float(row.distance or 0),
                "avg_speed": float(row.avg_speed or 0),
            })

    return {"activities": activities}

@app.delete("/delete/{activity_id}")
def delete_activity(activity_id: str):

    with engine.begin() as conn:
        result = conn.execute(
            text("""
            DELETE FROM activities
            WHERE id = :id
            RETURNING id
            """),
            {"id": activity_id}
        ).first()

    if result is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    return {
        "deleted_id": result.id,
        "status": "deleted"
    }

from mangum import Mangum

handler = Mangum(app)