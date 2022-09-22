It flask end-to-end API, where the server will invoked by sending the HTTP POST requests to API's endpoint.
The server uses postgresql and it stores the table in face_meta and embedding. The face_meta is about the person information and embedding stores the encoddings of image.
The server returns the top k matches in database of given images. It also stores the one image at a time using add_face and one or more using add_faces_in_bulk where we upload zip files.





How to execute:
In model I used postgresql in this you have to change the username and password in (psycopg2.coonect() ) model.py as well as main.py
Change app.config['UPLOAD_FOLDER']= path of this folder
step-1:
open postgresql shell create a database "flask_db" and connect to it.

Step-2:
open command prompt and run model.py i.e "python model.py"

Step-3:Run these Commands in Command prompt
set FLASK_APP=path of main.py in this folder
set FLASK_ENV=development
set FLASK_DEBUG=1
flask run

Step-4:
To test my server I used postman POST request 
for add_face set --> method as POST and URL as http://127.0.0.1:5000/add_face/. Go to Body and click formdata add first with key 'image' and upload image in value 
for search_faces --> method as POST and URL as http://127.0.0.1:5000/search_faces/. same as face_set but add one more row 'k' and value as mentioned in question
for add_faces_in_bulk --> method as POST and URL as http://127.0.0.1:5000/add_faces_in_bulk/. Go to Body and click formdata add first with key 'zipfile' and upload zip folder in value



