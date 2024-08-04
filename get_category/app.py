import json
import pymysql
from decimal import Decimal

# Configuración de la conexión a la base de datos
rds_host = "database-cafe-balu.cziym6ii4nn7.us-east-2.rds.amazonaws.com"
rds_user = "baluroot"
rds_password = "baluroot"
rds_db = "cafe_balu"

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, __):
    try:
        # Validar presencia del campo 'pathParameters' en el evento
        status = 0
        if 'pathParameters' in event:
            status = event['pathParameters'].get('status')
        else:
            status = None

        # Validar que el 'status' sea un entero si está presente
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "message": "INVALID_STATUS"
                    }),
                }

        result = get_all_categories(status)

        body = {
            "message": "CATEGORIES_FETCHED",
            "categories": result
        }

        return {
            "statusCode": 200,
            "body": json.dumps(body, default=decimal_to_float)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "INTERNAL_SERVER_ERROR",
                "error": str(e)
            }),
        }

def get_all_categories(status):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()

        if status == 0:
            cursor.execute("SELECT * FROM categories")
        else:
            cursor.execute("SELECT * FROM categories WHERE status = %s", (status,))

        result = cursor.fetchall()

        result = [dict(zip([column[0] for column in cursor.description], row)) for row in result]

        return result
    except Exception as e:
        raise
    finally:
        connection.close()