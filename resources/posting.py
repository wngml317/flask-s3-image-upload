from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from datetime import datetime
from config import Config
import boto3


class PostingResource(Resource) :
    def post(self) :
        # 1. 클라이언트로부터 데이터를 받아온다.
        # photo(file), content(text)


        if 'photo' not in request.files :
            return {'error' : '파일을 업로드하세요'}, 400

        file = request.files['photo']
        content = request.form['content']

        # 2. S3에 파일 업로드
        # 파일명을 우리가 변경해 준다.
        # 파일명은 유니크하게 만들어야 한다.
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':','_') + '.jpg'

        # 유저가 올린 파일의 이름을 내가 만든 파일명으로 변경
        file.filename = new_file_name

        # S3 에 업로드 하면 된다.
        # AWS의 라이브러리를 사용해야 한다.
        # 이 파이썬 라이브러리가 boto3 라이브러리다
        # boto3 라이브러리 설치
        # pip install boto3
        s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, aws_secret_access_key = Config.SECRET_ACCESS)        

        try :
            s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, 
                                ExtraArgs = {'ACL' : 'public-read', 'ContentType' : file.content_type})

        except Exception as e:
            return {'error' : str(e)}, 500

        # 3. DB에 저장
        try :
            # 1) DB에 연결
            connection = get_connection()

            # 2) 쿼리문 만들기
            query = '''insert into posting
                        (content, imgUrl)
                        values
                        (%s, %s);'''
            
            record = (content, new_file_name)

            # 3) 커서를 가져온다.
            cursor = connection.cursor()

            # 4) 쿼리문을 커서를 이용하여 실행
            cursor.execute(query, record)

            # 5) 커넥션을 커밋해준다. -> 디비에 영구적으로 반영
            connection.commit()

            # 6) 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503


        return {'result' : 'success'}
