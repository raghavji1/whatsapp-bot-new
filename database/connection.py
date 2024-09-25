import mysql.connector
from datetime import datetime
import csv
import os

now = datetime.now()
formatted_date_time = now.strftime('%Y-%m-%d %H:%M:%S')

# Establish the connection
conn = mysql.connector.connect(
    host=os.getenv('HOST_NAME'),
    user=os.getenv('USER_NAME'),
    password=os.getenv('PASSWORD'),
    database=os.getenv('DB_NAME')
)

# Function to run the query
def run_query(conn):
    try:
        # Use a context manager to ensure cursor is closed
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                CONCAT('https://www.balticshipping.com/job/', v.id) AS job_url,
                dp.name AS position_name,
                FROM_UNIXTIME(v.date_of_join) AS formatted_date,
                v.contract_duration,
                v.salary,
                dvt.vessel_type,
                dc.country
            FROM
                vacancies v
            INNER JOIN
                vacancies_notes vn ON vn.vacancie_id = v.id
            INNER JOIN
                d_vessel_types dvt ON dvt.id = v.vessel_type
            INNER JOIN
                d_countries dc ON dc.id = v.ship_flag
            INNER JOIN
                d_positions dp ON v.positions_id = dp.id
            WHERE
                FROM_UNIXTIME(v.date_of_join) >= CURDATE()
            ORDER BY
                v.date_of_join;

            """)
            results = cursor.fetchall()
            
            # Ensure the utils directory exists
            os.makedirs('utils', exist_ok=True)
            
            # Specify the file path within the utils folder
            file_path = os.path.join('database', 'data.csv')
            
            # Write the results to a CSV file
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write the header row (column names)
                writer.writerow(['job_url', 'position_name', 'date of joining', 'contract_duration', 'salary', 'vessel_type', 'country'])
                
                # Write data rows
                for row in results:
                    writer.writerow(row)
            
            print(f"Data successfully written to {file_path}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    except IOError as e:
        print(f"IOError: {e}")
    finally:
        conn.close()

# Run the query
run_query(conn)
