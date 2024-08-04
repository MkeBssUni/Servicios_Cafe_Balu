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


        # Validar que 'id' esté presente en pathParameters
        id_str = event['pathParameters'].get('id')
        if id_str is None:
            logger.warning("Missing fields: id")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS"
                }),
            }

            # Verificar que el ID no contiene caracteres especiales
        if re.search(r'[<>?#``]', id_str):
            logger.warning("Invalid characters in id")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_CHARACTERS"
                }),
            }

        # Validar que 'id' sea un número entero
        try:
            id = int(id_str)
        except ValueError:
            logger.warning("Invalid id: id must be an integer")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_ID"
                }),
            }

        # Validar que 'id' sea un entero positivo
        if id <= 0:
            logger.warning("Invalid id: id must be a positive integer")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_ID"
                }),
            }

        # Verificar que el ID existe en la base de datos
        if not id_exists_in_db(id):
            logger.warning("ID does not exist in database")
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({
                    "message": "ID_NOT_FOUND"
                }),
            }

        cancel_sale(id)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "SUCCESSFUL_CANCELLATION",
            }),
        }
    except pymysql.MySQLError as e:
        logger.error("MySQL error: %s", str(e))
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "DATABASE_ERROR",
                "error": str(e)
            }),
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "MISSING_FIELDS",
                "error": str(e)
            }),
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "INVALID_JSON_FORMAT"
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


def id_exists_in_db(id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales WHERE id = %s", (id,))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        logger.error("Database query error: %s", str(e))
        return False
    finally:
        connection.close()


def cancel_sale(id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE sales SET status = 0 WHERE id=%s", (id,))
        connection.commit()
    except Exception as e:
        logger.error("Database update error: %s", str(e))
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
            },
            "body": json.dumps({
                "message": "DATABASE_ERROR"
            }),
        }
    finally:
        connection.close()
