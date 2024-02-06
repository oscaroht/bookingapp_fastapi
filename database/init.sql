CREATE database bookingapp;

create schema app;

-- To do: Create application user that only has access to app schema

--drop table app.events;
create table app.events(
event_id SERIAL PRIMARY key,
event_name text not null,
event_start timestamp not null,
event_location text not null,
total_ticket_amount int not null check (total_ticket_amount > 0),
available_tickets int not null check (available_tickets > 0)
);

--drop table app.users;
create table app.users(
user_id SERIAL PRIMARY key,
created_at timestamp DEFAULT CURRENT_TIMESTAMP,
active bool default true,
email text unique not null,
first_name text,
last_name text,
password text null, -- user pays and gets an email. user is invited to create account
constraint unique_email unique(email)
);

--drop table app.bookings;
create table app.bookings(
booking_id SERIAL PRIMARY KEY,
ts timestamp DEFAULT CURRENT_TIMESTAMP,
event_id int REFERENCES app.events (event_id),
user_id int REFERENCES app.users (user_id),
number_of_tickets smallint
);