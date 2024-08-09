import json
import pymysql
from decimal import Decimal

rds_host = "database-cafe-balu.cziym6ii4nn7.us-east-2.rds.amazonaws.com"
rds_user = "baluroot"
rds_password = "baluroot"
rds_db = "cafe_balu"
def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    try:
       result = get_low_stock_products()
       return {
           "statusCode": 200,
           "headers": headers,
           "body": json.dumps({
               "message": "PRODUCTS_FETCHED",
               "products": result
           }, default=decimal_to_float)
       }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "INTERNAL_SERVER_ERROR",
                "error": str(e)
            }),
        }

def get_low_stock_products():
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("select * from products where stock <= 5 and status = 1;", ())
    result = cursor.fetchall()
    result = [dict(zip([column[0] for column in cursor.description], row)) for row in result]
    return result

def connect_to_database():
    try:
        connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
        return connection
    except pymysql.MySQLError as e:
        raise Exception("ERROR CONNECTING TO DATABASE: " + str(e))

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError