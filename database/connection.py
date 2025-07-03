import mysql.connector


# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="bj3zvh8q7qm8y9xqdsa2-mysql.services.clever-cloud.com",
        user="utedfcdyvjh6yyfg",
        password="PQbRbocKvnmtFvLvKchl",
        database="bj3zvh8q7qm8y9xqdsa2",
        port="3306"
    )

