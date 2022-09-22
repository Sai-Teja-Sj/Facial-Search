import os
import psycopg2
import pandas as pd 
import string 
import cv2 
import json
import shutil
from zipfile import ZipFile
import face_recognition as fr
import numpy as np 
from flask import Flask,request,flash
#import urllib.request
from deepface import DeepFace 
from werkzeug.utils import secure_filename
from deepface.commons import functions
from psycopg2.extensions import register_adapter, AsIs 
from retinaface import RetinaFace
psycopg2.extensions.register_adapter(np.float32,psycopg2._psycopg.AsIs)

model=DeepFace.build_model('Facenet')

ALLOWED_EXTENSIONS=set(['png', 'jpg', 'jpeg','gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ['png', 'jpg', 'jpeg','gif']

app=Flask(__name__)
app.config['UPLOAD_FOLDER']="C:\\Users\\USER\\New folder\\"
app.secret_key="dont know"
app.config['MAX_CONTENT_LENGTH']=16*1024*1024
def get_db_connection():
    conn=psycopg2.connect(host='localhost',database='flask_db',user='postgres',password='Sagi#5139')
    return conn


def Euclidean(row):
    src=np.array(row['embedding'])
    trg=np.array(row['target'])

    dist=(src- trg)
    return np.sqrt(np.sum(np.multiply(dist,dist)))

@app.route('/')

@app.route('/add_face/', methods=['POST','GET'])
def addface():
    if request.method =='POST':
        
        if 'image' not in request.files:
            return 'no file uploaded'
            #image=fr.load_image_file(file)
        file=request.files['image']
        if file.filename =='':
            return 'No image selected for uploading'
        if file and allowed_file(file.filename):
            filename=secure_filename(file.filename)
            filepath=os.path.join(app.config['UPLOAD_FOLDER'],'test.jpg')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],'test.jpg'))
            #flash('Image successfully uploaded')        
            #return "uploaded"
        else:
            #flash('Allowed image types are ->png,jpg,jpeg,gif')
            return 'wrong thing'    
            
        #name and version
        str = filename
        target=filename
        dict_table = str.maketrans('', '', string.digits)
        new_string = str.translate(dict_table)
        str=new_string.split(".")
        new_string=str[0]
        str=new_string.split("_")
        name=""
        for i in range(len(str)):
            if str[i].isdigit() :
                name=name+"\0"
                #name=name + str[i]+" "
            else:
                name=name + str[i]+" "  
        #name=str[0]+" "+str[1] #name 

        new_string=target.split("_")
        version=new_string[-1]
        str=version.split(".")
        version=str[0]

        msg="name:"+name+" version:"+version
        conn=get_db_connection()
        cur=conn.cursor()
        instances=[]
        facial_img=functions.preprocess_face(filepath,target_size=(160,160))
        
        embeddings=model.predict(facial_img)[0]
        cur.execute('INSERT INTO face_meta(name,version,location,filename,embedding)'
                    'VALUES(%s,%s,%s,%s,%s)',
                    (name,version,"",filename,embeddings.tobytes()))
        #insert_args=()
        conn.commit()

        cur.execute('SELECT * FROM face_meta ORDER BY id DESC limit 1')
        records=cur.fetchone()
        id = records[0]
        
        for i,embed in enumerate(embeddings):

            cur.execute('INSERT INTO embedding(face_id,dimension,value)'
                        'VALUES(%s,%s,%s)',
                        (id,i,embed))

        conn.commit()
        cur.close()
        conn.close()
        data={"status":"ok","body":"implememented"}
        return json.dumps(data)


    data={"status":"some error", "body":"what happened dotn know"}
    return json.dumps(data)


@app.route('/search_faces/', methods=['POST'])
def search_faces():
    if request.method =='POST':
        
        if 'image' not in request.files:
            return 'no file uploaded'
            #image=fr.load_image_file(file)
        file=request.files['image']
        if file.filename =='':
            return 'No image selected for uploading'
        if file and allowed_file(file.filename):
            filename=secure_filename(file.filename)
            filepath=os.path.join(app.config['UPLOAD_FOLDER'],'test.jpg')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],'test.jpg'))
            
        else:
            #flash('Allowed image types are ->png,jpg,jpeg,gif')
            return 'wrong thing' 

        test_img_path=filepath
        
        targ_img=functions.preprocess_face(test_img_path,target_size=(160,160))
        targ_img.shape
        

        target_embeddings=model.predict(targ_img)[0].tolist()
        

        conn=get_db_connection()
        cur=conn.cursor()
        
        k=request.form['k']
        stm="SELECT filename,embedding FROM face_meta"
        cur.execute(stm)
        results=cur.fetchall()
        
        instances=[]
        for result in results:
            filename=result[0]
            by_embedding=result[1]
            embedding=np.frombuffer(by_embedding,dtype='float32')

            instance=[]
            instance.append(filename)
            instance.append(embedding)

            instances.append(instance)

        result_df=pd.DataFrame(instances,columns=["filename","embedding"])

        tar_dup=np.array([target_embeddings,]*result_df.shape[0])
        result_df["target"] = tar_dup.tolist()
        #result_df=result_df.reindex(['filename','embedding','target'])
        result_df.head()
        
        result_df['distance'] = result_df.apply(Euclidean, axis = 1)
        result_df = result_df.sort_values(by = ['distance']).reset_index(drop = True)
        result_df = result_df.drop(columns = ["embedding", "target"])
    
        

       # result_t=result_t.sort_values(by=['distance'])


        list=[]
        k=int(k)
        for i in range(k):
            re_json={}
            re_json["filename"]=result_df["filename"][i]
            re_json["distance"]=result_df['distance'][i]
            list.append(re_json)
        rec={}
        rec["Matches"]=list
        body={}
        body["body"]=rec
        #print(body)
        #body["op"]=id
        return json.dumps(body)

#UPLOAD_FOLDER=os.path.dirname(os.path.realpath(__file__))

def allowed_filez(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in set(['zip'])
@app.route('/add_faces_in_bulk/',methods=['POST'])

def add_faces_in_bulk():
    if request.method =='POST':
        if 'zipfile' not in request.files:
            return 'No file'
        file=request.files['zipfile']
        UPLOAD_FOLDER=app.config['UPLOAD_FOLDER']
        if file.filename == '':
            return 'No sleelcted file'
        if file and allowed_filez(file.filename):
            filename=secure_filename(file.filename)
            #file.save(os.path.join(UPLOAD_FOLDER,filename))
            filepath=os.path.join(UPLOAD_FOLDER,filename)
            file.save(filepath)
            path1=os.path.join(app.config['UPLOAD_FOLDER'],'folder')
            '''if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],'folder')):
                shutil.rmtree(path1)
                for root, dirs, files in os.walk(path1):
                    for file in files:
                        os.remove(os.path.join(path1,file))
            else:
                os.mkdir(path1) '''

            with ZipFile(filepath,'r') as zip:
                zip.extractall('folder')


            #zip_ref=zipfile.ZipFile(os.path.join(UPLOAD_FOLDER,filename),'r')
            #zip_ref=extractall(UPLOAD_FOLDER,None,b'12345')
            #zip_ref.close()
            #return 'extracted'

            conn=get_db_connection()
            cur=conn.cursor()
            img_paths=[]
            j=int(0)
            for root,dir,files in os.walk(path1):
                for file in files:
                    if '.jpg' in file:
                        pathg=root+'\\'+file
                        #return path1
                        str = file
                        target=file
                        dict_table = str.maketrans('', '', string.digits)
                        new_string = str.translate(dict_table)
                        str=new_string.split(".")
                        new_string=str[0]
                        str=new_string.split("_")
                        name=""
                        for i in range(len(str)):
                            if str[i].isdigit() :
                                name=name + str[i]
                                name=name+" "
                                #name=str[0]+" "+str[1] #name
                            else:
                                name=name + str[i]
                                name=name+" "     
                        #name        

                        new_string=target.split("_") 
                        version=new_string[-1]
                        str=version.split(".")
                        version=str[0]
                        #version
                        


                        #fac_img=functions.preprocess_face(pathg,target_size=(160,160))
                        #fac_img.shape
                        facial_img=functions.preprocess_face(pathg,target_size=(160,160))
                        embedding=model.predict(facial_img)[0]
                        #embedd=model.predict(fac_img)[0]

                        cur.execute('INSERT INTO face_meta(name,version,location,filename,embedding)'
                                    'VALUES(%s,%s,%s,%s,%s)',
                                    (name,version,"",target,embedding.tobytes()))
                        
                        #insert_args=()
                        conn.commit()

                        cur.execute('SELECT * FROM face_meta ORDER BY id DESC limit 1')
                        records=cur.fetchone()
                        id = records[0]

                        for i,embed in enumerate(embedding):
                            cur.execute('INSERT INTO embedding(face_id,dimension,value)'
                                        'VALUES(%s,%s,%s)',
                                        (id,i,embed))

                        conn.commit()
                        j=j+1
            conn.commit()
            cur.close()
            conn.close()
            data={"status":"ok","body":"implememented"}
            return json.dumps(data)

            #return "guess worked "

    return 'Method should be POST'  #'''  
