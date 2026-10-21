import streamlit as st
st.set_page_config(page_title="Paper Trading Simulator", page_icon="📈", layout="wide") 
import pandas as pd
import yfinance as yf

def get_live_price(ticker):
    try:
        #create connection object to Yahoo Finance
        stock = yf.Ticker(ticker)
        
        #Fetch most recent trading period data
        data_today = stock.history(period='1d',interval='1m')
        
        #Grab the absolute latest "Close" price column number
        latest_price = data_today['Close'].iloc[-1]
        return float(latest_price)
    except Exception:
        #Returns None for invalid ticker
        return None

if "account_cash" not in st.session_state:
    st.session_state.account_cash = 10000.00
    
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
    
if "transaction_history" not in st.session_state:
    st.session_state.transaction_history = []
    
def buy_stock(ticker, shares_to_buy, current_price):
    #Total cost calculation    
    total_cost = shares_to_buy * current_price
    
    #Risk validation: check if capital exists
    if total_cost > st.session_state.account_cash:
        st.error("Transaction Denied: Insufficient Funds. Need ${total_cost:.2f}")
        return False
    
    #Capital deduction: subtract total cost from available balance    
    st.session_state.account_cash -= total_cost
    
    if ticker in st.session_state.portfolio:
        #Calculate new average cost basis for existing shares
        total_shares = portfolio[ticker]["shares"] + shares_to_buy
        old_total_cost = portfolio[ticker]["shares"] * portfolio[ticker]["avg_cost"]
        new_avg_cost = (old_total_cost + total_cost) / total_shares
        
        st.session_state.portfolio[ticker]["shares"] = total_shares
        st.session_state.portfolio[ticker]["avg_cost"] = new_avg_cost
    else:
        #Insert new ticker assets
        st.session_state.portfolio[ticker] = {
            "shares": shares_to_buy,
            "avg_cost": current_price
        }
        
    #Append event data to ledger    
    st.session_state.transaction_history.append({
        "Action": "BUY",
        "Ticker": ticker,
        "shares": shares_to_buy,
        "Price": f"${current_price:.2f}",
        "Total Cost": f"${total_cost:.2f}"
    })
    
    st.success(f"🎉 Successfully bought {shares_to_buy} shares of {ticker}!")
    return True
    

def sell_stock(ticker,shares_to_sell,current_price):
    global account_cash
    
    #Checks to see if ticker symbol is in portfolio
    if ticker not in portfolio:
        print("Error: No shares owned!")
        return False
        
    #Checks to see if enough shares are owned
    if shares_to_sell > portfolio[ticker]["shares"]:
        print("Error: not enough shares to sell")
        return False
        
    #Calculate earnings from the sale
    cash_gained = shares_to_sell * current_price
    
    #Update account balance
    account_cash += cash_gained
    
    #Subtract shares_to_sell from portfolio
    portfolio[ticker]["shares"] -= shares_to_sell
    
    #If shares owned is zero, delete ticker symbol from portfolio
    if portfolio[ticker]["shares"] == 0:
        del portfolio[ticker]
        
    #Add sell record to transaction_history
    transaction_history.append({
        "Action": "SELL",
        "Ticker": ticker,
        "Shares": shares_to_sell,
        "Price": f"${current_price:.2f}",
        "Total Return": f"${cash_gained:.2f}"        
    })    
    st.success(f"Successfully sold {shares_to_sell} shares of {ticker}!")
    return True
        
#Top panel calculations
portfolio_value = 0.0
for holding_ticker, assets in st.session_state.portfolio.items():
    current_market_price = get_live_price(holding_ticker)
    if current_market_price:
        portfolio_value += assets["shares"] * current_market_price
    else:
        portfolio_value += assets["shares"] * assets["avg_cost"]
        
total_net_worth = st.session_state.account_cash + portfolio_value
    
#Top row cards
st.title("📈 Stock Portfolio Trading Dashboard")
metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric(label="💵 Wallet Cash", value=f"${st.session_state.account_cash:,.2f}")
with metric_col2:
    st.metric(label="📊 Asset Value", value=f"${portfolio_value:,.2f}")
with metric_col3:
    st.metric(label="💲Net Worth", value=f"${total_net_worth:,.2f}")
    
st.divider()    

ui_col1, ui_col2 = st.columns(2)

with ui_col1:
    st.subheader("🔍 Stock Ticker Search")
    
    searched_ticker = st.text_input("Enter Stock Ticker Symbol:", value="COST").upper().strip()
    order_shares = st.number_input("Quantity:", min_value=1, step=1)
    
    if searched_ticker:
        target_price = get_live_price(searched_ticker)
        
    if target_price is not None:  
        st.metric(label=f"Current valuation for {searched_ticker}", value=f"${target_price:.2f}")
    
        #Interactive timeline chart
        st.write(f"📊 **{searched_ticker} Historical Valuation Chart (Last Week)**")
    try:
        #Fetches 5 day price history for selected stock
        chart_stock = yf.Ticker(searched_ticker)
        historical_df = chart_stock.history(period="5d",interval="1d")
        
        #Streamlit automatically plots the 'Close' price vector cleanly across the width
        st.line_chart(historical_df["Close"], use_container_width=True)
    except Exception:
        st.caption("Unable to generate chart")
    st.write("---")
        
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🟢 Execute Buy Order", use_container_width=True, type="primary"):
            buy_stock(searched_ticker, order_shares, target_price)
            st.rerun()
            
    with btn_col2:
        if st.button("🔴 Execute Sell Order", use_container_width=True):
            sell_stock(searched_ticker, order_shares, target_price)
            st.rerun()
            
with ui_col2:
    st.subheader("💼 Active Vault Positions")
    if st.session_state.portfolio:
        display_data = []
        for ticker, data in st.session_state.portfolio.items():
            live_p = get_live_price(ticker)
            if live_p is None:
                live_p = data["avg_cost"]
                
            current_val = data["shares"] * live_p
            cost_basis = data["shares"] * data["avg_cost"]
            pnl = current_val - cost_basis
            
            display_data.append({
                "Asset": ticker, "Shares": data["shares"],
                "Avg Entry": f"${data['avg_cost']:.2f}",
                "Value": f"${current_val:.2f}", "Profit/Loss": f"${pnl:.2f}"
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    else:
        st.info("Vault is empty. Place a buy order.")
        
st.divider()

st.subheader("📜 System Audit Log")
if st.session_state.transaction_history:
    st.dataframe(pd.DataFrame(st.session_state.transaction_history[::-1]), use_container_width=True, hide_index=True)
    
#Reset the dashboard
st.write("---")

with st.expander("⚠️ Advanced System Operations Management"):
    st.write("Wipe all simulation state engines to clear active memory cache blocks:")
    
    if st.button("🚨 Wipe Session Data & Reset Account Cash", use_container_width=True):
    
        st.session_state.account_cash = 10000.00
        st.session_state.portfolio = {}
        st.session_state.transaction_history = []
        
        st.toast("System variables cleared successfully! Reloading main framework...")
        
        st.rerun()