import requests
import json
import log
import oracledb
import mysql.connector
from mysql.connector import Error
import uuid


def getRequest(item):
    try:        

        # Define the SQL query to insert data into a table
        select_query = """
        SELECT * FROM CANTEEN_ITEM WHERE STATUS='1' 
        """

        if item != "":
            if item == "isTablet":
                select_query = select_query + " AND TABLETVIEW = 'YES' ORDER BY ORDERBY ASC"
            else:
                select_query = select_query + " AND ITEM = '" + item + "' ORDER BY ORDERBY ASC"
            # print(select_query)

            # Execute the insert query with the data
            cursor.execute(select_query)       
        else:
            select_query = select_query + "  ORDER BY ORDERBY ASC"
            cursor.execute(select_query)
        

        # Fetch column names
        columns = [col[0].lower() for col in cursor.description]

        # Fetch all rows and convert to list of dicts
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert to JSON
        json_data = json.dumps(rows, default=str)
            
        return json_data

    
    except oracledb.DatabaseError as e:
         error, = e.args
         log.infolog(f"Oracle-Error-Code: {error.code}")
         log.infolog(f"Oracle-Error-Message: {error.message}")
         return e


    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def testgetRequest(item):
    try:        
       
        # Create a cursor object
        cursor = connection.cursor()

        # Define the SQL query to insert data into a table
        select_query = """
        SELECT * FROM CANTEEN_ITEM2 WHERE STATUS='1' 
        """

        if item != "":
            if item == "isTablet":
                select_query = select_query + " AND TABLETVIEW = 'YES' ORDER BY ORDERBY ASC"
            else:
                select_query = select_query + " AND ITEM = '" + item + "' ORDER BY ORDERBY ASC"
            # print(select_query)

            # Execute the insert query with the data
            cursor.execute(select_query)       
        else:
            select_query = select_query + "  ORDER BY ORDERBY ASC"
            cursor.execute(select_query)
        

        # Fetch column names
        columns = [col[0].lower() for col in cursor.description]

        # Fetch all rows and convert to list of dicts
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert to JSON
        json_data = json.dumps(rows, default=str)
            
        return json_data

    
    except oracledb.DatabaseError as e:
         error, = e.args
         log.infolog(f"Oracle-Error-Code: {error.code}")
         log.infolog(f"Oracle-Error-Message: {error.message}")
         return e


    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()




def getRequestCategory():
    try:        
       
        # Create a cursor object
        cursor = connection.cursor()

        # Define the SQL query to insert data into a table
        select_query = """
        SELECT * FROM CANTEEN_ITEM_CATEGORY 
        """
        # Execute the insert query with the data
        cursor.execute(select_query)
        
        
        # Fetch column names
        columns = [col[0].lower() for col in cursor.description]

        # Fetch all rows and convert to list of dicts
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert to JSON
        json_data = json.dumps(rows, default=str)

            
        return json_data

    
    except oracledb.DatabaseError as e:
         error, = e.args
         log.infolog(f"Oracle-Error-Code: {error.code}")
         log.infolog(f"Oracle-Error-Message: {error.message}")
         return e


    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def postRequestSave(data):
    try:
        batch_id = str(uuid.uuid4())

        # print("Connection established successfully.")

        # Create a cursor object
        cursor = connection.cursor()

        # Define the SQL query to insert data into a table
        insert_query = """
        INSERT INTO CANTEEN_PAY (ITEM, PRICE, QTY, AMOUNT, PAYID, CREATEDATE, CREATEBY, IMGID, PAYMENTTYPE, TRANSACTIONID, ISMANUAL)
        VALUES (:1, :2, :3, :4, :5, SYSDATE, :6, :7, :8, :9, :10)
        """

        for item in data:
            # Define the data to be inserted
            data_to_insert = (item.get('item'), item.get('price'), item.get('qty'), item.get('amount'), batch_id, item.get('terminal'), item.get('imgid'), item.get('paymenttype'), item.get('transactionid'), item.get('ismanual'))

            # Execute the insert query with the data
            cursor.execute(insert_query, data_to_insert)

        # Commit the transaction
        connection.commit()

        # print("record insert successfully.")

        result = "success"        
        return result

    
    except oracledb.DatabaseError as e:
         error, = e.args
         log.infolog(f"Oracle-Error-Code: {error.code}")
         log.infolog(f"Oracle-Error-Message: {error.message}")
         return e


    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def getCheckMMEStar (id):
    try:
     
         # Create a cursor object
        cursor = connection.cursor()

        # Define the SQL query to insert data into a table
        select_query = "SELECT status FROM voucher_transaction where transaction_id = '" + id + "'"
        
        # Execute the insert query with the data
        cursor.execute(select_query)
        
        
        # Fetch column names
        columns = [col[0].lower() for col in cursor.description]

        # Fetch all rows and convert to list of dicts
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert to JSON
        json_data = json.dumps(rows)

            
        return json_data



    except Error  as e:
        
         log.infolog(f"mysql-Error: {e}")
         return e


    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
