<h1>bookingapp_fastapi</h1>

<h2>Description</h2>
A low-level minimalistic webapp for booking tickets for events written with FastAPI and raw SQL. Should only be used for demonstration purposes.

<h2>Technology</h2>
<p>I used FastAPI (incl. Pydantic) with raw SQL on a Postgres database. This experience was truly eye opening! The solution is so simple and elegant while being highly flexible and very well performant. 
  The implementation of raw SQL (over an ORM) results in much better query performance. Having this much controll of the database is something I absolutely love! I implemented psycopg2 features such as
  connection pooling and query optimization that would not be possible when using Django.
</p>
<p>
  I also prefer API architecture over server side rendering. I have always found server side rendering to be clumsy. Django's need for templates, form, models are just adding a lot of complexity to an 
  otherwise simple problem. FastAPI leans heavily on Pydantic, which is a data validation library. I was a bit scheptical about the benefit of Pydantic, at first. However, it proved to be extremely usefull. It guarantees a level of data integrety that I have only withnessed before
  in a database. Having that level of safety, while still being flexible contributed to a very high developer happiness.
</p>

<h2>Setup</h2>
<ul>
  <li>Create a new Python virtual environment</li>
  <li>Install dependencies: pip install -r requirements.txt</li>
  <li>Run: fastapi dev main.py</li>
</ul>
