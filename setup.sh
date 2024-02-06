#!/bin/bash
# this file contains instructions on how to build this project on a Linux machine
# this includes downloading the requirements, creating the database tables, and starting the server

# NOT COMPLETE. NEEDS TESTING.

uvicorn main:app --log-config=logging.conf