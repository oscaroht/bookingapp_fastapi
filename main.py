from datetime import datetime
from fastapi import FastAPI, HTTPException
import logging
import logging.config as log_config
from psycopg2.errors import CheckViolation
from psycopg2.extras import RealDictRow  # imported for type hinting
from pydantic import BaseModel, field_validator
import re
from typing import List

import config  # not used but needed to check if the environment variables load before server starts
from db import DatabaseConnection
from user import router as user_router


# setup loggers
log_config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger('app')

# setup default loggers
# https://gist.github.com/liviaerxin/d320e33cbcddcc5df76dd92948e5be3b


app = FastAPI()
app.include_router(user_router)

# Server start
# uvicorn main:app --reload --reload-delay 5 --log-config=logging.conf


class Booking(BaseModel):
    booking_id: int
    ts: datetime
    event_id: int
    user_id: int
    number_of_tickets: int


class CreateBooking(BaseModel):
    event_id: int
    first_name: str
    last_name: str
    email: str
    number_of_tickets: int

    @field_validator("email")
    def is_email(cls, value: str) -> str:
        """Check for invalid email"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        is_valid = re.fullmatch(pattern, value)
        if not is_valid:
            raise ValueError('Email not valid.')
        return value

    @field_validator("number_of_tickets")
    def is_number_of_tickets(cls, value: int) -> int:
        """The number of tickets ordered cannot be smaller than 0."""
        if value <= 0:
            raise ValueError("Number of tickets has to be larger than 0.")
        return value

    @field_validator("event_id")
    def is_event_id(cls, value: int) -> int:
        """Check if get_event_by_id throws an exception. If so than the validation
        for the booking fails."""
        if value <= 0:
            raise ValueError("Number of tickets has to be larger than 0.")
        try:
            get_event_by_id(value)
        except EventNotFoundError:
            raise
        return value


class BookingError(Exception):
    """Custom error class to handle booking errors. The error messages in this class are passed to users
    directly so please make then understandable to users."""
    pass


def get_booking_by_id(booking_id: int) -> Booking:
    with DatabaseConnection() as db:
        query = "SELECT * FROM app.bookings WHERE booking_id = %(booking_id)s;"
        db.cursor.execute(query, {'booking_id': booking_id})
        booking = db.cursor.fetchone()
        db.cursor.connection.commit()
    if not booking:
        raise BookingError(f"No booking with id {booking_id} found.")
    return Booking(**booking)


def create_booking(new_booking: CreateBooking) -> int:
    with DatabaseConnection() as db:
        try:
            db.cursor.execute("""
                    -- lower the number of available tickets
                    UPDATE app.events SET
                    available_tickets = available_tickets - %(number_of_tickets)s
                    WHERE event_id = %(event_id)s;
                    
                    -- create user if needed
                    insert into app.users(email, first_name, last_name)
                    VALUES ( %(email)s, %(first_name)s, %(last_name)s)
                    ON CONFLICT ON CONSTRAINT unique_email DO NOTHING;
                    
                    -- insert booking
                    INSERT INTO app.bookings(
                    event_id, 
                    user_id,
                    number_of_tickets
                    ) 
                    SELECT %(event_id)s, (select user_id from app.users where email = %(email)s), %(number_of_tickets)s
                    RETURNING booking_id;
                    """, dict(new_booking))
        except CheckViolation:
            logger.error(f"Not enough tickets available for booking {new_booking}")
            raise BookingError("Not enough tickets available.")

        booking: RealDictRow = db.cursor.fetchone()  # dict like object
        db.cursor.connection.commit()
    return booking['booking_id']


class EventError(Exception):
    """Custom error class to handle event errors. The error messages in this class are passed to users
    directly so please make then understandable to users."""
    pass


class EventNotFoundError(EventError):
    """Custom error class to handle missing event errors. The error messages in this class are passed to users
    directly so please make then understandable to users."""
    pass


class Event(BaseModel):
    event_name: str
    event_start: datetime
    event_location: str
    total_ticket_amount: int
    available_tickets: int

    @field_validator("total_ticket_amount")
    def is_total_ticket_amount(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("The total number of tickets has to be larger than 0.")
        return value


def get_event_by_id(event_id: int) -> Event:
    with DatabaseConnection() as db:
        query = "SELECT * FROM app.events WHERE event_id = %(event_id)s;"
        db.cursor.execute(query, {'event_id': event_id})
        event = db.cursor.fetchone()
        db.cursor.connection.commit()
    if not event:
        raise EventNotFoundError(f"No event with id {event_id} found")
    return Event(**event)


def get_event_list() -> List[Event]:
    with DatabaseConnection() as db:
        query = "SELECT * FROM app.events;"
        db.cursor.execute(query)
        events = db.cursor.fetchall()
        db.cursor.connection.commit()
    return [Event(**event) for event in events]


@app.get("/")
async def root():
    return {"message": "Welcome to this booking app. This app allows you to book tickets "
                       "for various events. To get a list of events call GET /events/. To get "
                       "details about a specific event call GET /events/{id}. To order tickets "
                       "call POST /booking"}


@app.get("/events")
async def rout():
    try:
        return get_event_list()
    except Exception:
        logger.error("Unable to get events.", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to obtain event list")


@app.get("/event/{event_id}")
async def get_event(event_id: int):
    try:
        return get_event_by_id(event_id)
    except EventError as err:
        logger.warning(f"Bad request.", exc_info=True)
        raise HTTPException(status_code=422, detail=str(err))
    except Exception:
        logger.error(f"Unable to get event {event_id}.")
        raise HTTPException(status_code=500, detail=f"Unable to get event with id {event_id}.")


@app.post("/booking")
async def post_booking(new_booking: CreateBooking):
    try:
        return create_booking(new_booking)
    except BookingError as err:
        logger.warning(f"Bad request.", exc_info=True)
        raise HTTPException(status_code=422, detail=str(err))
    except Exception:
        logger.error("Issue while creating the booking or retrieving the booking id", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to create booking or retrieve booking id.")


@app.get("/booking/{booking_id}")
async def get_booking(booking_id):
    try:
        return get_booking_by_id(booking_id)
    except BookingError as err:
        logger.warning(f"Bad request.", exc_info=True)
        raise HTTPException(status_code=422, detail=str(err))
    except Exception:
        logger.error(f"Unable to get booking {booking_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to get booking.")
