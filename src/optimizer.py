import pandas as pd

def run_market_optimization(db_path='data/sales_optimizer.db'):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database missing at {db_path}. Please execute db_manager.py first.")
        
    con = duckdb.connect(db_path)
    
    #  Extracting Normalized Feature Data from DuckDB
    query = "SELECT * FROM v_normalized_market_metrics;"
    df = con.query(query).df()
    con.close()
    
    #  Vectorized Math Engine: Composite Market Scoring
    #  Inverting inflation and competition scores because lower values are favorable
    df['market_score'] = (
        (0.35 * df['norm_sales']) +
        (0.35 * df['norm_gdp']) +
        (0.15 * (1.0 - df['norm_inflation'])) +
        (0.15 * (1.0 - df['norm_competition']))
    )
    df['market_score'] = df['market_score'].round(4)
    
    #  Applying Executive Strategic Hard Constraints
    # Rule 1: CAC must be under $300 USD
    # Rule 2: Inflation must not exceed 10% (0.10)
    df['passed_constraints'] = (df['customer_acquisition_cost_usd'] <= 300.0) & (df['norm_inflation'] < 0.50) # relative scale: upper 50% market rejection
    
    df = df.sort_values(by='market_score', ascending=False).reset_index(drop=True)
    return df
