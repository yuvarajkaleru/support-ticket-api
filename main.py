from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from dotenv import load_dotenv
import os

from database import engine, get_db, Base
from models import Ticket, User,Comment
from schemas import TicketCreate, TicketResponse, UserCreate, UserLogin,TicketUpdate,TicketStatus,CommentCreate,CommentResponse

from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
from jose import jwt , JWTError

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Customer Support Ticket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
Base.metadata.create_all(bind=engine)
# app

load_dotenv()

pwd_context= CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):  # sourcery skip: dict-assign-update-to-union, inline-immediately-returned-variable, simplify-dictionary-update
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

    except JWTError:
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

def check_ticket_access(ticket: Ticket, current_user: User):
    # sourcery skip: merge-duplicate-blocks

    if current_user.role == "admin":
        return

    if current_user.role == "agent":
        if ticket.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    elif current_user.role == "customer":
        if ticket.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

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
    search: str | None = None,
    status: TicketStatus | None = None,
    priority: str | None = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket)

    if current_user.role == "admin":
        pass

    elif current_user.role == "agent":
        query = query.filter(
            Ticket.assigned_to == current_user.id
        )

    else:
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    if search:
        query = query.filter(
            Ticket.title.ilike(f"%{search}%")
        )

    if status:
        query = query.filter(
            Ticket.status == status.value
        )

    if priority:
        query = query.filter(
            Ticket.priority == priority
        )

    query = query.order_by(Ticket.created_at.desc())

    return query.offset(skip).limit(limit).all()



@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    check_ticket_access(ticket, current_user)

    return ticket

@app.put("/tickets/{ticket_id}",response_model=TicketResponse)
def update_ticket(
                ticket_id : int,
                ticket_data : TicketUpdate,
                db : Session = Depends(get_db),
                current_user : User = Depends(get_current_user)
                ):
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404,detail="Ticket Not Found")
    check_ticket_access(ticket, current_user)
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
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if ticket is None:
        raise HTTPException(status_code=404,detail="Ticket Not Found")
    check_ticket_access(ticket, current_user)
    db.delete(ticket)
    db.commit()

    return {"message":"ticket deleted successfully"}

@app.post("/register")
def register_user(user_data : UserCreate,db: Session = Depends(get_db)):
    # sourcery skip: use-named-expression
    existing_user = db.query(User).filter(User.username == user_data.username).first()

    if existing_user:
        raise HTTPException(status_code=400,detail="User Already Exists")

    hashed_password = pwd_context.hash(user_data.password)

    new_user = User(username = user_data.username,hashed_password = hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
    "message": "User Registered Successfully",
    "username": new_user.username,
    "role": new_user.role
    }


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

@app.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentResponse
)
def create_comment(
    ticket_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    check_ticket_access(ticket, current_user)

    new_comment = Comment(
        content=comment_data.content,
        ticket_id=ticket_id,
        user_id=current_user.id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

@app.get(
    "/tickets/{ticket_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # sourcery skip: inline-immediately-returned-variable
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    check_ticket_access(ticket, current_user)

    comments = (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments

@app.get("/users/me")
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/",
    StaticFiles(directory=BASE_DIR / "frontend", html=True),
    name="frontend"
)