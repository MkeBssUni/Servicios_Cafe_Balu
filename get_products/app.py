import json
import pymysql
from decimal import Decimal

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
        status = None

        if 'pathParameters' in event and 'status' in event['pathParameters']:
            status = int(event['pathParameters']['status'])


        if status != 0 and status != 1:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "INVALID_STATUS"
                }),
            }

        result = get_all_products(status)

        body = {
            "message": "PRODUCTS_FETCHED",
            "products": result
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

def get_all_products(status):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        if status == 0:
            cursor.execute("select p.*, c.name as category_name from products p inner join categories c on p.category_id = c.id;")
        else:
            cursor.execute("select p.*, c.name as category_name from products p inner join categories c on p.category_id = c.id WHERE c.status = %s", (status,))

        connection.commit()

        result = cursor.fetchall()
        result = [dict(zip([column[0] for column in cursor.description], row)) for row in result]

        return result
    except Exception as e:
        raise e
    finally:
        connection.close()
