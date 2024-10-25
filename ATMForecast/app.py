import os
from dotenv import load_dotenv, set_key
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from sqlalchemy import create_engine, text, Table, Column, String, MetaData, DateTime, Integer, Float, Boolean, Date
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import logging
from db_utils import setup_database_connections, get_last_record_id, refresh_data, test_connection
from urllib.parse import quote_plus
import uuid
import time
import calendar
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')  # Use environment variable for secret key

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize local SQLite database
local_engine = create_engine('sqlite:///AMANReporting.db')
metadata = MetaData()

# Create LastUpdated table if it doesn't exist
LastUpdated = Table('LastUpdated', metadata,
    Column('id', String, primary_key=True),
    Column('timestamp', DateTime)
)

# Create all tables
metadata.create_all(local_engine)

# Create a separate engine for app configuration
app_config_engine = create_engine('sqlite:///app_config.db')
app_config_metadata = MetaData()

# Define the Tables table in the app configuration database
ConfigTables = Table('ConfigTables', app_config_metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('update_column', String, nullable=False)
)

# Add this new table definition
CustomQueries = Table('CustomQueries', app_config_metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('sql_query', String, nullable=False),
    Column('update_column', String, nullable=False)
)

# Add this new table definition after CustomQueries
KPIConfigurations = Table('KPIConfigurations', app_config_metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('table_name', String, nullable=False),
    Column('calculation_field', String, nullable=False),
    Column('calculation_method', String, nullable=False),
    Column('time_spans', String, nullable=False),  # Store as JSON string
    Column('conditions', String, nullable=False)   # Store as JSON string
)

# Create the tables in the app configuration database
app_config_metadata.create_all(app_config_engine)

def get_db_connection():
    logger.info("Getting database connection")
    conn = sqlite3.connect('atm_forecasting.db')
    conn.row_factory = sqlite3.Row
    logger.info("Database connection established")
    return conn

def get_config():
    logger.info("Fetching configuration from environment variables")
    config = {
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'db_name': os.environ.get('DB_NAME'),
        'db_username': os.environ.get('DB_USERNAME'),
        'db_password': os.environ.get('DB_PASSWORD')
    }
    # Log the config without the password
    safe_config = {k: v if k != 'db_password' else '********' for k, v in config.items()}
    logger.info(f"Configuration fetched: {safe_config}")
    return config

def get_remote_engine():
    logger.info("Creating remote database engine")
    config = get_config()
    db_user = config['db_username']
    db_password = quote_plus(config['db_password'])
    db_host = config['host']
    db_port = config['port']
    db_name = config['db_name']

    # Use pymssql for SQL Server
    db_url = f"mssql+pymssql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    logger.debug(f"Database URL: {db_url.replace(db_password, '********')}")

    try:
        engine = create_engine(db_url, pool_timeout=30, pool_pre_ping=True)
        logger.info("Remote database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Failed to create remote database engine: {str(e)}")
        raise

def get_last_updated():
    logger.info("Fetching last update timestamp")
    conn = get_db_connection()
    try:
        result = conn.execute('SELECT timestamp FROM LastUpdated WHERE id = "last_refresh"').fetchone()
        conn.close()
        if result:
            logger.info(f"Last update timestamp: {result['timestamp']}")
            return result['timestamp']
        logger.info("No last update timestamp found")
        return "Never"
    except sqlite3.OperationalError:
        logger.warning("LastUpdated table not found")
        return "Never"

def update_last_updated():
    logger.info("Updating last update timestamp")
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute('CREATE TABLE IF NOT EXISTS LastUpdated (id TEXT PRIMARY KEY, timestamp TEXT)')
    conn.execute('INSERT OR REPLACE INTO LastUpdated (id, timestamp) VALUES (?, ?)', ("last_refresh", now))
    conn.commit()
    conn.close()
    logger.info(f"Last update timestamp set to: {now}")

@app.context_processor
def inject_last_updated():
    return dict(last_updated=get_last_updated())

def is_db_configured():
    logger.info("Checking if database is configured")
    config = get_config()
    required_keys = ['host', 'port', 'db_name', 'db_username', 'db_password']
    is_configured = all(config.get(key) for key in required_keys)
    logger.info(f"Database configured: {is_configured}")
    return is_configured

@app.route('/')
def index():
    logger.info("Accessing landing page")
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    logger.info("Accessing settings page")
    if request.method == 'POST':
        logger.info("Processing POST request for settings")
        config = {
            'host': request.form['host'],
            'port': request.form['port'],
            'db_name': request.form['db_name'],
            'db_username': request.form['db_username'],
            'db_password': request.form['db_password']
        }
        
        for key, value in config.items():
            os.environ[f'DB_{key.upper()}'] = value
            set_key('.env', f'DB_{key.upper()}', value)
        
        logger.info("Database configuration updated")
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    
    config = get_config()
    
    with app_config_engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM ConfigTables"))
        added_tables = result.fetchall()
        
        result = connection.execute(text("SELECT * FROM CustomQueries"))
        custom_queries = result.fetchall()
    
    return render_template('settings.html', config=config, added_tables=added_tables, custom_queries=custom_queries)

@app.route('/test_db_connection')
def test_db_connection_route():
    logger.info("Testing database connection")
    try:
        engine = get_remote_engine()
        if test_connection(engine):
            return jsonify({"message": "Connection successful!"}), 200
        else:
            return jsonify({"error": "Connection failed"}), 500
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_db_structure')
def get_db_structure():
    logger.info("Fetching database structure")
    try:
        engine = get_remote_engine()
        inspector = inspect(engine)
        
        structure = []
        for table_name in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns(table_name)]
            structure.append({
                "id": table_name,
                "text": table_name,
                "children": [{"id": f"{table_name}.{col}", "text": col} for col in columns]
            })
        
        return jsonify(structure)
    except Exception as e:
        logger.error(f"Error fetching database structure: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/add_table', methods=['POST'])
def add_table():
    logger.info("Adding new table")
    table_name = request.form['table_name']
    update_column = request.form['update_column']
    
    try:
        with app_config_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO ConfigTables (name, update_column) VALUES (:name, :update_column)"),
                {"name": table_name, "update_column": update_column}
            )
        flash(f'Table {table_name} added successfully', 'success')
    except IntegrityError:
        flash(f'Table {table_name} already exists', 'error')
    except Exception as e:
        logger.error(f"Error adding table: {str(e)}")
        flash(f'Error adding table: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/delete_table/<int:table_id>', methods=['POST'])
def delete_table(table_id):
    logger.info(f"Deleting table with ID: {table_id}")
    max_retries = 5
    retry_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            with app_config_engine.begin() as conn:
                result = conn.execute(
                    text("SELECT name FROM ConfigTables WHERE id = :id"),
                    {"id": table_id}
                ).fetchone()
                
                if result is None:
                    flash('Table not found', 'error')
                    return redirect(url_for('settings'))
                
                table_name = result[0]
                
                conn.execute(
                    text("DELETE FROM ConfigTables WHERE id = :id"),
                    {"id": table_id}
                )
            
            flash(f'Table {table_name} deleted successfully', 'success')
            return redirect(url_for('settings'))

        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.exception(f"Error deleting table after {attempt + 1} attempts: {str(e)}")
                flash(f'Error deleting table: {str(e)}', 'error')
                return redirect(url_for('settings'))

        except Exception as e:
            logger.exception(f"Error deleting table: {str(e)}")
            flash(f'Error deleting table: {str(e)}', 'error')
            return redirect(url_for('settings'))

    flash('Failed to delete table due to database lock', 'error')
    return redirect(url_for('settings'))

@app.route('/add_custom_query', methods=['POST'])
def add_custom_query():
    logger.info("Adding new custom query")
    query_name = request.form['query_name']
    sql_query = request.form['sql_query']
    update_column = request.form['update_column']
    
    try:
        # Test the query first
        source_engine = get_remote_engine()
        with source_engine.connect() as conn:
            result = conn.execute(text(sql_query))
            # Fetch a few rows to make sure it works
            rows = result.fetchmany(5)
        
        # If we get here, the query executed successfully
        with app_config_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO CustomQueries (name, sql_query, update_column) VALUES (:name, :sql_query, :update_column)"),
                {"name": query_name, "sql_query": sql_query, "update_column": update_column}
            )
        flash(f'Custom query "{query_name}" added successfully', 'success')
    except IntegrityError:
        flash(f'Custom query "{query_name}" already exists', 'error')
    except Exception as e:
        logger.error(f"Error adding custom query: {str(e)}")
        flash(f'Error adding custom query: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/delete_custom_query/<int:query_id>', methods=['POST'])
def delete_custom_query(query_id):
    logger.info(f"Deleting custom query with ID: {query_id}")
    try:
        with app_config_engine.begin() as conn:
            result = conn.execute(
                text("SELECT name FROM CustomQueries WHERE id = :id"),
                {"id": query_id}
            ).fetchone()
            
            if result is None:
                flash('Custom query not found', 'error')
                return redirect(url_for('settings'))
            
            query_name = result[0]
            
            conn.execute(
                text("DELETE FROM CustomQueries WHERE id = :id"),
                {"id": query_id}
            )
        
        flash(f'Custom query "{query_name}" deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting custom query: {str(e)}")
        flash(f'Error deleting custom query: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/refresh_data', methods=['POST'])
def refresh_data_route():
    logger.info("Starting data refresh process")
    try:
        source_engine = get_remote_engine()
        
        # Fetch custom queries
        with app_config_engine.connect() as conn:
            custom_queries = conn.execute(text("SELECT * FROM CustomQueries")).fetchall()
        
        # Refresh data for regular tables
        refresh_data(source_engine, local_engine, app_config_engine)
        
        # Refresh data for custom queries
        for query in custom_queries:
            try:
                logger.info(f"Executing custom query: {query.name}")
                with source_engine.connect() as conn:
                    df = pd.read_sql(query.sql_query, conn)
                
                # Save the result to the local database
                df.to_sql(query.name, local_engine, if_exists='replace', index=False)
                logger.info(f"Custom query {query.name} executed and saved successfully")
            except Exception as e:
                logger.error(f"Error executing custom query {query.name}: {str(e)}")
        
        update_last_updated()
        flash('Data refreshed successfully', 'success')
    except Exception as e:
        logger.error(f"Error refreshing data: {str(e)}")
        flash(f'Error refreshing data: {str(e)}', 'error')
    return redirect(url_for('index'))

# Add this near the top of app.py, after creating the Flask app
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/stats/config', methods=['GET', 'POST'])
def stats_config():
    if request.method == 'POST':
        try:
            kpi_data = {
                'name': request.form['kpi_name'],
                'table_name': request.form['table_name'],
                'calculation_field': request.form['calculation_field'],
                'calculation_method': request.form['calculation_method'],
                'time_spans': request.form.getlist('time_spans[]'),
                'conditions': request.form.getlist('conditions[]')
            }
            
            with app_config_engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO KPIConfigurations 
                        (name, table_name, calculation_field, calculation_method, time_spans, conditions) 
                        VALUES (:name, :table_name, :calculation_field, :calculation_method, :time_spans, :conditions)
                    """),
                    {
                        'name': kpi_data['name'],
                        'table_name': kpi_data['table_name'],
                        'calculation_field': kpi_data['calculation_field'],
                        'calculation_method': kpi_data['calculation_method'],
                        'time_spans': json.dumps(kpi_data['time_spans']),
                        'conditions': json.dumps(kpi_data['conditions'])
                    }
                )
            flash('KPI configuration added successfully', 'success')
        except Exception as e:
            flash(f'Error adding KPI configuration: {str(e)}', 'error')
        return redirect(url_for('stats_config'))
    
    # Get existing KPI configurations
    with app_config_engine.connect() as conn:
        kpis = conn.execute(text("SELECT * FROM KPIConfigurations")).fetchall()
    
    # Get available tables from local database
    inspector = inspect(local_engine)
    available_tables = inspector.get_table_names()
    
    return render_template('stats_config.html', 
                         kpis=kpis, 
                         available_tables=available_tables,
                         calculation_methods=['Count', 'Distinct Count', 'Sum', 'Average', 'Maximum', 'Minimum'],
                         time_span_pairs=[
                             ('Today', 'Yesterday'),
                             ('Month to Date', 'Last Month to Date'),
                             ('Year to Date', 'Last Year to Date')
                         ])

@app.route('/get_table_columns/<table_name>')
def get_table_columns(table_name):
    try:
        inspector = inspect(local_engine)
        columns = [column['name'] for column in inspector.get_columns(table_name)]
        return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_kpi/<int:kpi_id>', methods=['POST'])
def delete_kpi(kpi_id):
    try:
        with app_config_engine.begin() as conn:
            conn.execute(
                text("DELETE FROM KPIConfigurations WHERE id = :id"),
                {"id": kpi_id}
            )
        flash('KPI configuration deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting KPI configuration: {str(e)}', 'error')
    return redirect(url_for('stats_config'))

# Add this near the top of app.py with the other imports
import json

# Add this with your other template filters
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []

@app.route('/calculate_kpis')
def calculate_kpis():
    try:
        with app_config_engine.connect() as conn:
            kpis = conn.execute(text("SELECT * FROM KPIConfigurations")).fetchall()
        
        results = []
        for kpi in kpis:
            time_spans = json.loads(kpi.time_spans)
            conditions = json.loads(kpi.conditions) if kpi.conditions else []
            
            for current_period, comparison_period in time_spans:
                # Calculate the date ranges
                current_range = get_date_range(current_period)
                comparison_range = get_date_range(comparison_period)
                
                # Build and execute the query for both periods
                current_value = calculate_kpi_value(kpi, current_range, conditions)
                comparison_value = calculate_kpi_value(kpi, comparison_range, conditions)
                
                # Calculate the change percentage
                if comparison_value and comparison_value != 0:
                    change = ((current_value - comparison_value) / comparison_value) * 100
                else:
                    change = 0
                
                results.append({
                    'name': f"{kpi.name} ({current_period})",
                    'current_value': format_value(current_value),
                    'comparison_period': comparison_period,
                    'change': round(change, 1)
                })
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error calculating KPIs: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_date_range(period):
    today = datetime.now().date()
    
    if period == 'Today':
        return (today, today)
    elif period == 'Yesterday':
        yesterday = today - timedelta(days=1)
        return (yesterday, yesterday)
    elif period == 'Month to Date':
        return (today.replace(day=1), today)
    elif period == 'Last Month to Date':
        last_month = today.replace(day=1) - timedelta(days=1)
        return (last_month.replace(day=1), last_month)
    elif period == 'Year to Date':
        return (today.replace(month=1, day=1), today)
    elif period == 'Last Year to Date':
        last_year = today.replace(year=today.year-1)
        return (last_year.replace(month=1, day=1), last_year)
    
    return (today, today)

def calculate_kpi_value(kpi, date_range, conditions):
    query = f"SELECT {get_calculation_sql(kpi.calculation_method, kpi.calculation_field)} "
    query += f"FROM {kpi.table_name} "
    query += f"WHERE DATE(RecordDateEntry) BETWEEN :start_date AND :end_date"
    
    if conditions:
        for condition in conditions:
            query += f" AND {condition['field']} {condition['operator']} :value"
    
    try:
        with local_engine.connect() as conn:
            params = {
                'start_date': date_range[0],
                'end_date': date_range[1]
            }
            if conditions:
                for i, condition in enumerate(conditions):
                    params[f'value_{i}'] = condition['value']
            
            result = conn.execute(text(query), params).scalar()
            return result or 0
    except Exception as e:
        logger.error(f"Error calculating KPI value: {str(e)}")
        return 0

def get_calculation_sql(method, field):
    if method == 'Count':
        return 'COUNT(*)'
    elif method == 'Distinct Count':
        return f'COUNT(DISTINCT {field})'
    elif method == 'Sum':
        return f'SUM({field})'
    elif method == 'Average':
        return f'AVG({field})'
    elif method == 'Maximum':
        return f'MAX({field})'
    elif method == 'Minimum':
        return f'MIN({field})'
    return 'COUNT(*)'

def format_value(value):
    if isinstance(value, (int, float)):
        return '{:,.0f}'.format(value)
    return str(value)

if __name__ == '__main__':
    logger.info("Starting ATM Forecasting application")
    app.run(debug=True)
