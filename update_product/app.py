import json
import pymysql
import logging
import re

rds_host = "database-cafe-balu.cziym6ii4nn7.us-east-2.rds.amazonaws.com"
rds_user = "baluroot"
rds_password = "baluroot"
rds_db = "cafe_balu"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    try:
        claims = event['requestContext']['authorizer']['claims']
        role = claims['cognito:groups']

        if 'admin' not in role:
            return {
                "statusCode": 403,
                "headers": headers,
                "body": json.dumps({
                    "message": "FORBIDDEN"
                }),
            }

        if 'body' not in event:
            logger.error("Request body not found in the event")
            raise KeyError('body')

        body = json.loads(event['body'])

        product_id = body.get('id')
        name = body.get('name')
        stock = body.get('stock')
        price = body.get('price')
        status = body.get('status')
        image = body.get('image')
        category_id = body.get('category_id')

        if not product_id or not name or not stock or not price or not status or not image or not category_id:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS",
                }),
            }

        if is_invalid_image(image):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_IMAGE",
                }),
            }

        if not category_exists(category_id):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "CATEGORY_NOT_FOUND",
                }),
            }

        update_product(product_id, name, stock, price, status, image, category_id)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "PRODUCT_UPDATED",
            }),
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "MISSING_KEY",
                "error": str(e)
            }),
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


def update_product(product_id, name, stock, price, status, image, category_id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    print(connection)
    try:
        cursor = connection.cursor()
        cursor.execute("""
                UPDATE products 
                SET name=%s, stock=%s, price=%s, status=%s, image=%s, category_id=%s 
                WHERE id=%s
            """, (name, stock, price, status, image, category_id, product_id))
        connection.commit()
        logger.info("Product updated successfully with id=%s", product_id)
    except Exception as e:
        logger.error("Database update error: %s", str(e))
        raise
    finally:
        connection.close()

def category_exists(category_id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories WHERE id = %s", (category_id,))
        connection.commit()
        return cursor.fetchone()[0] > 0

    except Exception as e:
        logger.error("Database select error: %s", str(e))
        raise e
    finally:
        connection.close()

def product_exists_in_category(category_id, name,product_id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s AND lower(name) = %s and id != %s", (category_id, name.lower(), product_id))
        connection.commit()
        return cursor.fetchone()[0] > 0

    except Exception as e:
        logger.error("Database select error: %s", str(e))
        raise e
    finally:
        connection.close()

def is_invalid_image(image):
    pattern = r"^data:image/(png|jpg|jpeg);base64,([a-zA-Z0-9+/=]+)$"
    return not re.match(pattern, image)