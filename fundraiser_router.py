from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from create_tables import get_db
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from models import Fundraise
from pydantic import BaseModel



router = APIRouter(prefix='/api/fundraiser', tags=["api"])

class FundraiserCreate(BaseModel):
    title: str
    description: str
    raised_money: float
    finished: bool
    start_date: datetime = None
    end_date: datetime = None

@router.post('/create')
async def create(data: FundraiserCreate , db = Depends(get_db)):
    fundraise = Fundraise(
        title = data.title,
        description = data.description,
        raised_money = data.raised_money,
        finished = data.finished,
        start_date = data.start_date,
        end_date = data.end_date
    )
    db.add(fundraise)
    db.commit()
    db.refresh(fundraise)
    return {"message": "Fundraiser created successfully", "id": fundraise.id}
