from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from dotenv import load_dotenv
import os

from database import engine, get_db, Base
from models import Ticket, User
from schemas import TicketCreate, TicketResponse, UserCreate, UserLogin,TicketUpdate,TicketStatus

from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
from jose import jwt , JWTError


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Support Ticket API")

load_dotenv()

pwd_context= CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return encoded_jwt

def get_current_user(token : str = Depends(oauth2_scheme), db : Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})

    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user

def require_role(required_role: str):
    def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return current_user

    return role_checker

@app.post("/tickets",response_model=TicketResponse)
def create_ticket(
    ticket : TicketCreate,
    db : Session = Depends(get_db), 
    current_user : User = Depends(get_current_user)
    ):

    new_ticket = Ticket(
        title = ticket.title,
        description = ticket.description,
        priority = ticket.priority,
        user_id = current_user.id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


@app.get("/tickets", response_model=list[TicketResponse])
def get_tickets(
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
    ):

    if current_user.role == "admin":
        tickets = db.query(Ticket).all()
    elif current_user.role == "agent":
        db.query(Ticket).filter(Ticket.assigned_to == current_user.id).all()
    else:
        tickets = db.query(Ticket).filter(Ticket.user_id == current_user.id).all()
    return tickets


@app.get("/tickets/{ticket_id}",response_model=TicketResponse)
def get_ticket(
    ticket_id : int,
    db : Session = Depends(get_db),
    curent_user : User = Depends(get_current_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id,Ticket.user_id == curent_user.id).first()
    if ticket is None:
        raise HTTPException(status_code=404,detail="No ticket found")

    return ticket

@app.put("/tickets/{ticket_id}",response_model=TicketResponse)
def update_ticket(
                ticket_id : int,
                ticket_data : TicketUpdate,
                db : Session = Depends(get_db),
                current_user : User = Depends(get_current_user)
                ):
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id,Ticket.user_id==current_user.id).first()
    if ticket is None:
        raise HTTPException(status_code=404,detail="Ticket Not Found")

    update_data = ticket_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value)

    ticket.updated_at = datetime.now(timezone.utc) 
    db.commit()
    db.refresh(ticket)

    return ticket


@app.delete("/tickets/{ticket_id}")
def delete_ticket(
    ticket_id : int,
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
    ):
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id,Ticket.user_id==current_user.id).first()

    if ticket is None:
        raise HTTPException(status_code=404,detail="Ticket Not Found")
    
    db.delete(ticket)
    db.commit()

    return {"message":"ticket deleted successfully"}

@app.post("/register")
def register_user(user_data : UserCreate,db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()

    if existing_user:
        raise HTTPException(status_code=400,detail="User Already Exists")

    hashed_password = pwd_context.hash(user_data.password)

    new_user = User(username = user_data.username,hashed_password = hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message":"User Registered Successfully"}


@app.post("/login")
def login(user_data : OAuth2PasswordRequestForm = Depends() , db : Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not pwd_context.verify(user_data.password,user.hashed_password):

        raise HTTPException(status_code=401,detail="Invalid Username or Password")

    access_token = create_access_token(data={"sub":user.username})

    return {"access_token": access_token,"token_type":"bearer"}

@app.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(require_role("admin"))):
    return {"message": "Welcome Admin"}

@app.get("/agent/dashboard")
def agent_dashboard(current_user: User = Depends(require_role("agent"))):
    return {"message": "Welcome Support Agent"}

@app.put("/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id : int,agent_id : int,db :Session = Depends(get_db),current_user : User = Depends(require_role("admin"))):

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if ticket is None:
        raise HTTPException(status_code=404,detail="Ticket Not Found")
    agent = db.query(User).filter(User.id == agent_id,User.role == "agent").first()

    if agent is None:
        raise HTTPException(status_code=404,detail="Agent Not Found")

    
    ticket.assigned_to = agent_id

    db.commit()
    db.refresh(ticket)

    return {"message":"Ticket assigned successfully"}