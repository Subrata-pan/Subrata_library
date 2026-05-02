#!/usr/bin/env python3
"""
Database Inspection Script for KitabGhar
Shows the complete structure of the SQLite database
"""

import sqlite3
import os

def inspect_database(show_sample_rows=True):
    """Inspect and display the database structure"""
    db_path = "instance/kitabghar.db"

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("📊 KitabGhar Database Structure")
        print("=" * 50)

        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            print("-" * 30)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            if columns:
                print(f"{'CID':<3} {'Name':<20} {'Type':<15} {'NotNull':<8} {'PK':<3} {'Default':<10}")
                print("-" * 70)
                for col in columns:
                    cid, name, col_type, notnull, default, pk = col
                    nullable = "NO" if notnull else "YES"
                    primary = "YES" if pk else "NO"
                    default_val = str(default) if default is not None else "NULL"
                    print(f"{cid:<3} {name:<20} {col_type:<15} {nullable:<8} {primary:<3} {default_val:<10}")
            else:
                print("No columns found")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"\n📈 Total rows: {count}")

            # Optionally show first 5 rows
            if show_sample_rows and count > 0:
                print(f"\n🔍 First 5 rows from {table_name}:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                if rows:
                    # Get column names for header
                    column_names = [col[1] for col in columns]
                    print(" | ".join(f"{name:<15}" for name in column_names))
                    print("-" * (len(column_names) * 18))
                    for row in rows:
                        formatted_row = []
                        for value in row:
                            if value is None:
                                formatted_row.append("NULL".ljust(15))
                            else:
                                str_value = str(value)
                                if len(str_value) > 12:
                                    str_value = str_value[:9] + "..."
                                formatted_row.append(str_value.ljust(15))
                        print(" | ".join(formatted_row))
                else:
                    print("No data in table")

        conn.close()

    except sqlite3.Error as e:
        print(f"❌ SQLite error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == '__main__':
    inspect_database()
