import os
import boto3
import uvicorn
import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, File, UploadFile, Query
#from fastapi import *
from fastapi.templating import Jinja2Templates

# 加载 .env 文件
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# AWS RDS settings
db_rds = mysql.connector.pooling.MySQLConnectionPool(
    pool_name = "sql_pool",
    host=os.getenv("AWS_RDS_HOSTNAME"),
    user=os.getenv("AWS_RDS_USER"),
    password=os.getenv("AWS_RDS_PASSWORD"),
    database="messagePhoto")



def get_first_ten_contents(page):

    try:

        con = db_rds.get_connection()
        Cursor = con.cursor(dictionary=True)
        page_size = 20
        start = page * 10

        sql = '''SELECT message, photoURL FROM (SELECT message, photoURL FROM messages ORDER BY id DESC) AS subquery LIMIT %s, %s;'''
        Cursor.execute(sql, (start, page_size))
        contents = Cursor.fetchall()

        if len(contents) > 10:

            return {'nextPage': page+1,
                    'data': contents[:10]}
        elif len(contents) < 11 and len(contents) > 0:

            return {'nextPage': None,
                    'data': contents}
        
        else:

            return {'error': True,
                    'message': '請輸入留言圖片資料正確頁數'}
        
    except mysql.connector.Error as err:

        return {'error': True,
                'message': err}
    
    finally:

        con.close()
        Cursor.close()

# home page
@app.get("/")
async def index(request: Request):

    return templates.TemplateResponse(request=request, name="page.html")

# homepage get the messages and images
@app.get("/api/contents")
async def load_previous_content(page: int = Query(0)):

    contents = get_first_ten_contents(page)

    return contents


# insert message and image url into rds db
def save_data_to_rds(msg, img_url):

    try:
        con = db_rds.get_connection()
        Cursor = con.cursor(dictionary=True)

        insert_msg_img = '''INSERT INTO messages (message, photoURL) VALUES (%s, %s);'''
        msg_img = (msg, img_url)

        Cursor.execute(insert_msg_img, msg_img)
        con.commit()

        return True

    except Exception as e:

        return False
    
    finally:

        con.close()
        Cursor.close()



# save photo in aws s3 and photo url & message in aws rds
@app.post("/api/uploading")
async def upload_message_photo(message: str = Form(...), file: UploadFile = File(...)):

    img_input = await file.read()

    # AWS S3 settings
    session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
    )
    s3 = session.client('s3')

    # S3 bucket & photo id
    bucket_name = os.getenv('AWS_BUCKET_NAME')
    s3_object_key = f'photo/{file.filename}'

    # upload photo to S3
    s3.put_object(Bucket=bucket_name, Key=s3_object_key, Body=img_input, ContentType=file.content_type)

    # save message, photo_url in aws rds
    img_url = f"https://{os.getenv('AWS_CLOUDFRONT_DOMAIN')}/{s3_object_key}"
    if save_data_to_rds(message, img_url):

        result_json = get_first_ten_contents(0)

        return result_json
    
    else:

        return {'error': True}

# save message, photo_url in aws rds

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
