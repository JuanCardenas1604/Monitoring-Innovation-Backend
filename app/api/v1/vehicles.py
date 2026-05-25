from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/vehicles", tags=["Vehículos"])


@router.get("/", response_model=VehicleListResponse)
def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None, min_length=1, description="Búsqueda global en marca, localidad y aspirante"),
    brand: Optional[str] = Query(None, min_length=1),
    location: Optional[str] = Query(None, min_length=1),
    applicant: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Vehicle)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Vehicle.brand.ilike(pattern),
                Vehicle.location.ilike(pattern),
                Vehicle.applicant.ilike(pattern),
            )
        )

    if brand:
        query = query.filter(Vehicle.brand.ilike(f"%{brand}%"))
    if location:
        query = query.filter(Vehicle.location.ilike(f"%{location}%"))
    if applicant:
        query = query.filter(Vehicle.applicant.ilike(f"%{applicant}%"))

    query = query.order_by(Vehicle.created_at.desc())
    total = query.count()
    vehicles = query.offset(skip).limit(limit).all()
    return VehicleListResponse(
        items=[VehicleResponse.model_validate(v) for v in vehicles],
        total=total,
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )
    return VehicleResponse.model_validate(vehicle)


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    update_data = vehicle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    db.delete(vehicle)
    db.commit()
