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
from models import UserFundraise, Fundraise
from pydantic import BaseModel
from sqlalchemy import select


router = APIRouter(prefix='/api/users', tags=["api"])
router_chuj = APIRouter(tags=['main'])
class donationsInfo(BaseModel):
    user_id: int
    fundraise_id: int
    points: float

@router.post('/api/donate', tags=['api'])
async def donation(data: donationsInfo, db=Depends(get_db)):
    q = select(Fundraise.finished).where(Fundraise.id == data.fundraise_id)
    result = db.execute(q)
    if not result.scalars().first():
        return {
            'chuj': "zbiorka sie zakonczyla debilu"
        }
    else:
        donation = UserFundraise(
            user_id=data.user_id,
            fundraise_id=data.fundraise_id,
            money_summary=data.points
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)
        return {"message": "Donation added successfully", "id": donation.id}



@router_chuj.get('/charities', tags=['main'])
async def view_charities(db=Depends(get_db)):
   return [
        {
            'id': i.id,
            'title': i.title,
            'description': i.description,
            'raised_money': i.raised_money,
            'finished': i.finished,
            'start_date': i.start_date,
            'end_date': i.end_date,
            'target_money': i.target_money
        }
        for i in db.query(Fundraise).all()
    ]


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Fundraise, User, UserFundraise
from typing import Optional


@router_chuj.get('/charities/{charity_id}', tags=['main'])
async def get_charity_detail(charity_id: int, db: Session = Depends(get_db)):
    charity = db.query(Fundraise).filter(Fundraise.id == charity_id).first()

    if not charity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zbiórka nie została znaleziona"
        )

    contributors_count = db.query(UserFundraise).filter(
        UserFundraise.fundraise_id == charity_id
    ).count()

    top_contributor = db.query(UserFundraise, User).join(
        User, UserFundraise.user_id == User.id
    ).filter(
        UserFundraise.fundraise_id == charity_id
    ).order_by(
        UserFundraise.money_summary.desc()
    ).first()

    organizer_name = top_contributor[1].username if top_contributor else "Nieznany"

    return {
        'id': charity.id,
        'title': charity.title,
        'description': charity.description,
        'raised_money': float(charity.raised_money) if charity.raised_money else 0.0,
        'target_money': float(charity.target_money) if charity.target_money else 0.0,
        'finished': charity.finished,
        'start_date': charity.start_date.isoformat() if charity.start_date else None,
        'end_date': charity.end_date.isoformat() if charity.end_date else None,
        'organizer': organizer_name,
        'contributors_count': contributors_count
    }


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Fundraise, User, UserFundraise
from typing import Optional
from pydantic import BaseModel


class DonationRequest(BaseModel):
    user_id: int
    fundraise_id: int
    amount: float
    company: str


@router_chuj.post('/donate', tags=['main'])
async def make_donation(donation: DonationRequest, db: Session = Depends(get_db)):
    """
    Wpłata na zbiórkę - aktualizuje stan zbiórki i dodaje wpis o darowiźnie
    """
    try:
        # Znajdź zbiórkę
        fundraise = db.query(Fundraise).filter(Fundraise.id == donation.fundraise_id).first()

        if not fundraise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zbiórka nie została znaleziona"
            )

        # Sprawdź czy zbiórka nie jest zakończona
        if fundraise.finished:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zbiórka jest już zakończona"
            )

        # Sprawdź czy użytkownik istnieje
        user = db.query(User).filter(User.id == donation.user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Użytkownik nie został znaleziony"
            )

        # Sprawdź czy kwota jest dodatnia
        if donation.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kwota musi być większa od zera"
            )

        # Aktualizuj raised_money w zbiórce (konwersja Decimal -> float -> Decimal)

        current_raised = float(fundraise.raised_money) if fundraise.raised_money else 0.0
        new_raised = current_raised + donation.amount
        user = select(User).where(User.id == donation.user_id).first()
        user.total_spent += donation.amount
        fundraise.raised_money = float(str(new_raised))


        # Sprawdź czy istnieje już wpis dla tego użytkownika i zbiórki
        existing_donation = db.query(UserFundraise).filter(
            UserFundraise.user_id == donation.user_id,
            UserFundraise.fundraise_id == donation.fundraise_id
        ).first()

        if existing_donation:
            # Aktualizuj istniejącą wpłatę
            current_money = float(existing_donation.money_summary) if existing_donation.money_summary else 0.0
            new_money = current_money + donation.amount
            existing_donation.money_summary = float(str(new_money))
        else:
            # Utwórz nową wpłatę
            new_donation = UserFundraise(
                user_id=donation.user_id,
                fundraise_id=donation.fundraise_id,
                money_summary=float(str(donation.amount))
            )
            db.add(new_donation)

        # Sprawdź czy zbiórka osiągnęła cel
        if fundraise.target_money and new_raised >= float(fundraise.target_money):
            fundraise.finished = True

        # Aktualizuj total_spent użytkownika (konwersja Decimal -> float -> Decimal)
        current_spent = float(user.total_spent) if user.total_spent else 0.0
        new_spent = current_spent + donation.amount
        user.total_spent = float(str(new_spent))

        # Commit transakcji
        db.commit()

        # Refresh obiektów po commit
        db.refresh(fundraise)
        db.refresh(user)

        return {
            'success': True,
            'message': 'Wpłata została zrealizowana pomyślnie',
            'fundraise': {
                'id': fundraise.id,
                'raised_money': float(fundraise.raised_money),
                'target_money': float(fundraise.target_money) if fundraise.target_money else None,
                'finished': fundraise.finished
            },
            'user': {
                'id': user.id,
                'total_spent': float(user.total_spent)
            }
        }

    except HTTPException:
        # Ponownie podnieś HTTPException bez zmian
        raise
    except Exception as e:
        # Rollback w przypadku błędu
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas realizacji wpłaty: {str(e)}"
        )




