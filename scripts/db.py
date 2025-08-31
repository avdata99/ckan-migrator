"""
We have a really old PSQL instance running on docker (port 9133).
This Python script allows you to connect and extract all tables information
and data.
"""

import psycopg2
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any


class PSQL:
    def __init__(self, host='localhost', port=9133, dbname='old_ckan_db',
                 user='postgres', password='password'):
        """
        Initialize the database extractor with connection parameters.
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        Establish connection to the PostgreSQL database.
        """
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            dbname = self.connection_params['dbname']
            print(f"Successfully connected to database: {dbname}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def disconnect(self):
        """
        Close database connection.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")

    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database (excluding system tables).
        """
        query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """
        try:
            self.cursor.execute(query)
            tables = [row[0] for row in self.cursor.fetchall()]
            print(f"Found {len(tables)} tables in the database.")
            return tables
        except psycopg2.Error as e:
            print(f"Error fetching tables: {e}")
            return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table.
        """
        # Get column information
        column_query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
        """

        # Get row count
        count_query = f'SELECT COUNT(*) FROM "{table_name}";'

        try:
            # Get columns
            self.cursor.execute(column_query, (table_name,))
            columns = []
            for row in self.cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2],
                    'default': row[3],
                    'max_length': row[4]
                })

            # Get row count
            self.cursor.execute(count_query)
            row_count = self.cursor.fetchone()[0]

            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count
            }
        except psycopg2.Error as e:
            print(f"Error getting info for table {table_name}: {e}")
            return {}

    def extract_table_data(self, table_name: str,
                           limit: int = None) -> pd.DataFrame:
        """
        Extract all data from a specific table.
        """
        query = f'SELECT * FROM "{table_name}";'
        if limit:
            query += f" LIMIT {limit}"

        try:
            # Read data with string conversion for problematic types
            df = pd.read_sql_query(query, self.conn)

            # Handle datetime overflow issues proactively
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]':
                    # Check for potential overflow values
                    try:
                        # Try to identify problematic dates
                        # Dates before 1677 or after 2262 can cause issues
                        min_date = df[col].min()
                        max_date = df[col].max()
                        if pd.isna(min_date) or pd.isna(max_date):
                            continue
                    except (OverflowError, ValueError,
                            pd.errors.OutOfBoundsDatetime):
                        # Convert problematic datetime columns to strings
                        print(f"Warning: Converting datetime column '{col}' "
                              f"in table '{table_name}' to string due to "
                              "overflow issues")
                        df[col] = df[col].astype(str)

            print(f"Extracted {len(df)} rows from table '{table_name}'")
            return df
        except Exception as e:
            print(f"Error extracting data from table {table_name}: {e}")
            return pd.DataFrame()

    def save_table_data(self, table_name: str, df: pd.DataFrame,
                        output_dir: str = "extracted_data"):
        """
        Save table data to different formats (CSV, JSON).
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save as CSV
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        try:
            df.to_csv(csv_path, index=False)
            print(f"Saved {table_name} CSV data to {csv_path}")
        except Exception as e:
            print(f"Error saving CSV for {table_name}: {e}")

        # Save as JSON with datetime handling
        json_path = os.path.join(output_dir, f"{table_name}.json")
        try:
            # Create a copy for JSON export with datetime conversion
            df_json = df.copy()

            # Convert datetime columns to strings to avoid overflow issues
            for col in df_json.columns:
                if df_json[col].dtype == 'datetime64[ns]' or \
                   pd.api.types.is_datetime64_any_dtype(df_json[col]):
                    df_json[col] = df_json[col].astype(str)
                elif df_json[col].dtype == 'object':
                    # Handle mixed types that might contain dates
                    try:
                        # Check if any values look like timestamps
                        sample_vals = df_json[col].dropna().head(5)
                        if len(sample_vals) > 0:
                            for val in sample_vals:
                                if pd.api.types.is_datetime64_any_dtype(
                                        pd.to_datetime(val, errors='ignore')):
                                    df_json[col] = df_json[col].astype(str)
                                    break
                    except Exception:
                        # If there's any issue, convert to string to be safe
                        pass

            df_json.to_json(json_path, orient='records', indent=2)
            print(f"Saved {table_name} JSON data to {json_path}")
        except Exception as e:
            print(f"Error saving JSON for {table_name}: {e}")
            # Try alternative JSON export method
            try:
                # Fallback: convert all problematic columns to strings
                df_safe = df.copy()
                for col in df_safe.columns:
                    if df_safe[col].dtype in ['datetime64[ns]', 'object']:
                        df_safe[col] = df_safe[col].astype(str)

                df_safe.to_json(json_path, orient='records', indent=2)
                print(f"Saved {table_name} JSON data to {json_path} "
                      "(fallback)")
            except Exception as e2:
                msg = f"Failed to save JSON for {table_name} even with "
                msg += f"fallback: {e2}"
                print(msg)
                # Create a simple JSON with just the error info
                error_data = {
                    "error": f"Could not export {table_name} to JSON",
                    "original_error": str(e),
                    "fallback_error": str(e2),
                    "row_count": len(df),
                    "columns": list(df.columns)
                }
                with open(json_path, 'w') as f:
                    json.dump(error_data, f, indent=2)
                print(f"Saved error info for {table_name} to {json_path}")

    def generate_database_report(self, tables_info: List[Dict]) -> str:
        """
        Generate a comprehensive report about the database structure.
        """
        report = []
        report.append("# CKAN Database Analysis Report")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report.append(f"Generated on: {timestamp}")
        report.append(f"Database: {self.connection_params['dbname']}")
        report.append(f"Total tables: {len(tables_info)}")
        report.append("\n## Tables Summary\n")

        total_rows = 0
        for table_info in tables_info:
            if table_info:
                table_name = table_info['table_name']
                row_count = table_info['row_count']
                column_count = len(table_info['columns'])
                total_rows += row_count

                report.append(f"### {table_name}")
                report.append(f"- Rows: {row_count:,}")
                report.append(f"- Columns: {column_count}")
                report.append("")

                # Column details
                report.append("**Columns:**")
                for col in table_info['columns']:
                    is_null = col['nullable'] == 'YES'
                    nullable = "NULL" if is_null else "NOT NULL"
                    col_type = col['type']
                    col_name = col['name']
                    report.append(f"- `{col_name}` ({col_type}) {nullable}")
                report.append("")

        report.append("\n## Summary Statistics")
        report.append(f"- Total rows across all tables: {total_rows:,}")
        avg_rows = total_rows // len(tables_info) if tables_info else 0
        report.append(f"- Average rows per table: {avg_rows:,}")

        return "\n".join(report)

    def extract_all_data(self, save_data: bool = True, row_limit: int = None, filename_prefix: str = ""):
        """
        Main method to extract all database information and data.
        """
        if not self.connect():
            return

        try:
            # Get all tables
            tables = self.get_all_tables()
            if not tables:
                print("No tables found in the database.")
                return

            # Get detailed info for each table
            tables_info = []
            extracted_data = {}

            for table in tables:
                print(f"\nProcessing table: {table}")
                table_info = self.get_table_info(table)
                if table_info:
                    tables_info.append(table_info)

                    # Extract data if requested
                    if save_data:
                        df = self.extract_table_data(table, limit=row_limit)
                        if not df.empty:
                            extracted_data[table] = df
                            self.save_table_data(table, df)

            # Generate and save report
            report = self.generate_database_report(tables_info)
            report_filename = f"{filename_prefix}database_report.md"
            with open(report_filename, "w") as f:
                f.write(report)
            print(f"\nDatabase report saved to: {report_filename}")

            # Save tables info as JSON
            json_filename = f"{filename_prefix}tables_info.json"
            with open(json_filename, "w") as f:
                json.dump(tables_info, f, indent=2, default=str)
            print(f"Tables information saved to: {json_filename}")

            print("\n=== EXTRACTION COMPLETE ===")
            print(f"Processed {len(tables)} tables")
            if save_data:
                print(f"Data saved for {len(extracted_data)} tables")
            print("Check the 'extracted_data' directory for CSV and JSON "
                  "files")

        finally:
            self.disconnect()
