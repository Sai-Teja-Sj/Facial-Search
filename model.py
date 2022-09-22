import os
import psycopg2

conn = psycopg2.connect(
        host="localhost",
        database="flask_db",
        user="postgres",
        password="Sagi#5139")

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a command: this creates a new table
cur.execute('DROP TABLE IF EXISTS face_meta;')
cur.execute('CREATE TABLE face_meta (id serial PRIMARY KEY,'
                                 'name varchar (150) ,'
                                 'version varchar(100),'
                                 'location varchar(100),'
                                 'filename varchar(100),'
                                 'embedding bytea,'
                                 'date date DEFAULT CURRENT_TIMESTAMP);'
                                 )

cur.execute('DROP TABLE IF EXISTS embedding;') 
cur.execute('CREATE TABLE embedding(face_id int,'
                                    'dimension int,'
                                    'value numeric(30,5));'
                                    )                                

# Insert data into the table
conn.commit()

cur.close()
conn.close()






