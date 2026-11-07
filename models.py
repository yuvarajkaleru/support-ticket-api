from sqlalchemy import String,Text,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime, timezone
from database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id : Mapped[int] = mapped_column(primary_key=True,index=True)
    title : Mapped[str] = mapped_column(String(100))
    description : Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="open")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=True)
    owner: Mapped["User"] = relationship(back_populates="tickets",foreign_keys=[user_id])

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))

    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"),nullable=True)

class User(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True,index=True)
    username : Mapped[str] = mapped_column(String(50),unique=True,index=True)
    hashed_password : Mapped[str] = mapped_column(String(255))
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="owner",foreign_keys="Ticket.user_id")
    role: Mapped[str] = mapped_column(default="customer",nullable=False)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"),nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))