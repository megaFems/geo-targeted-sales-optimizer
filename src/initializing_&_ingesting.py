import os
import duckdb

def initialize_database(db_path='data/sales_optimizer.db', data_dir='data'):
    print(f"Connecting to database at: {db_path}")
    con = duckdb.connect(db_path)
    
    # Defining file target paths
    macro_csv = os.path.join(data_dir, 'raw_macro_trends.csv')
    sales_csv = os.path.join(data_dir, 'raw_sales_velocity.csv')
    
    # Ingesting Raw Datasets into Staging Tables
    print("Ingesting staging datasets into relational tables...")
    con.execute(f"""
        CREATE OR REPLACE TABLE staging_macro AS 
        SELECT * FROM read_csv_auto('{macro_csv}');
    """)
    
    con.execute(f"""
        CREATE OR REPLACE TABLE staging_sales AS 
        SELECT * FROM read_csv_auto('{sales_csv}');
    """)
    
    # Building Analytical Normalization View
    # Normalization formula: (x - min) / (max - min)
    print("Creating normalized analytical view: v_normalized_market_metrics...")
    con.execute("""
        CREATE OR REPLACE VIEW v_normalized_market_metrics AS 
        WITH bounds AS (
            SELECT 
                MIN(m.gdp_growth_rate) AS min_gdp, MAX(m.gdp_growth_rate) AS max_gdp,
                MIN(m.inflation_rate) AS min_inf, MAX(m.inflation_rate) AS max_inf,
                MIN(s.historical_sales_usd) AS min_sales, MAX(s.historical_sales_usd) AS max_sales,
                MIN(s.competitor_density_score) AS min_comp, MAX(s.competitor_density_score) AS max_comp
            FROM staging_macro m
            JOIN staging_sales s ON m.region_id = s.region_id
        )
        SELECT 
            m.region_id,
            m.country,
            m.city,
            s.historical_sales_usd,
            
            -- Min-Max Normalization Calculations
            CASE 
                WHEN (b.max_sales - b.min_sales) = 0 THEN 0.0
                ELSE ROUND((s.historical_sales_usd - b.min_sales) / (b.max_sales - b.min_sales), 4)
            END AS norm_sales,
            
            CASE 
                WHEN (b.max_gdp - b.min_gdp) = 0 THEN 0.0
                ELSE ROUND((m.gdp_growth_rate - b.min_gdp) / (b.max_gdp - b.min_gdp), 4)
            END AS norm_gdp,
            
            CASE 
                WHEN (b.max_inf - b.min_inf) = 0 THEN 0.0
                ELSE ROUND((m.inflation_rate - b.min_inf) / (b.max_inf - b.min_inf), 4)
            END AS norm_inflation,
            
            CASE 
                WHEN (b.max_comp - b.min_comp) = 0 THEN 0.0
                ELSE ROUND((s.competitor_density_score - b.min_comp) / (b.max_comp - b.min_comp), 4)
            END AS norm_competition,
            
            s.customer_acquisition_cost_usd
            
        FROM staging_macro m
        JOIN staging_sales s ON m.region_id = s.region_id
        CROSS JOIN bounds b;
    """)
    
    print(" Database and Analytical Views initialized successfully.")
    con.close()

if __name__ == "__main__":
    initialize_database()
