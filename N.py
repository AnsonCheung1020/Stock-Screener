
import pandas as pd
import datetime as dt
import yfinance as yf
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Get the CSV file name from the user
csvfilename = "3B_Total.csv"

# Load the stock symbols from the CSV file
stocklist = pd.read_csv(csvfilename, engine="python", encoding="ISO-8859-1")  # encoding= "UTF-8" is similar

# Set up yfinance
yf.pdr_override()
start = dt.datetime.now() - dt.timedelta(days=200)
now = dt.datetime.now()

#green candle
def green_candle(data, i): # positive i
    return (data['Close'][-i] > data['Close'][-i-1])
    
#red candle
def red_candle(data, i): # positive i
    return (data['Close'][-i] < data['Close'][-i-1])

#find maximum High between [start, end] 区间高点
def find_max_high(data, start, end):
    return (data['High'][-start:-end-1:-1].max())  # find the maximum between -2 to end, when the step is negative, the stop index should be less than the start index --> using reverse order is more readable 


#find mnimimum Low between [start, end] 区间低点
def find_min_low(data, start, end):
    return (data['Low'][-start:-end-1:-1].min())  # find the minimum between -2 to end

# check if there is formation of upward wedge 向上契型,第四次破顶 -> max_high is a green candle
def upward_wedge(data, start, end, max_high): # positive start, end (upthrust)
    if start <= 1: # start must be >= 2
        return False
    
    else:
        # count the number of peaks between -2 to end        
        peak_count = 0        
        for i in range(-start, -end-1, -1):
            
            if 1.005 * max_high >= data['High'].iloc[i] >= 0.995 * max_high: #range of peak: [1.005 to 0.995]
                peak_count += 1
                #print(f"Peak @{i} = {data['High'].iloc[i]}, {peak_count}")
                #i +=1               
                if peak_count >= 4 and data['Close'].iloc[-1] > 1.005 * max_high: # break up from peak after 4 attempts and consider the retest entry point 
                    #print(f"Break up!")
                    return True

        return False
       
# check if there is formation of downward wedge 向下契型,第四次破底 -> min_low is a red candle 
def downward_wedge(data, start, end, min_low): # positive start, end (downthrust)
    if start <= 1: # start must be >= 2
        return False
    
    else:
        # count the number of peaks between -2 to end        
        low_count = 0        
        for i in range(-start, -end-1, -1):
            
            if 0.995 * min_low <= data['Low'].iloc[i] <= 1.005 * min_low: #range of trough: [1.005 to 0.995]--> it has considered both increasing lower lines and decreasing lower lines 
                low_count += 1
                #print(f"Trough @{i} = {data['Low'].iloc[i]}, {low_count}")
                #i +=1   
                      
                if low_count >= 4 and data['Close'].iloc[-1] < 0.995 * min_low: # break down from trough after 4 attempts and consider the retest entry point 
                    #print(f"Break down!")
                    return True

        return False
#consider [0.995 - 1.005 ] as the effective range of wedge formation by considering its consolidation 
    
# Calculate the moving average
def calculate_ma_slope(data, ma_window, bar_number):
    ma = data['Close'].rolling(ma_window).mean()
    ma_slope = (ma[-1] - ma[-bar_number]) / (bar_number - 1)
    return ma, ma_slope

# volume decrease ladder 三连上升梯量
def volume_decrease_ladder3(data, i):
    if data['Volume'].iloc[-i-2] > data['Volume'].iloc[-i-1] > data['Volume'].iloc[-i]:        
        return True
    else:
        return False
    
# volume increase ladder 三连下降梯量
def volume_increase_ladder3(data, i):
    if data['Volume'].iloc[-i-2] < data['Volume'].iloc[-i-1] < data['Volume'].iloc[-i]:        
        return True
    else:
        return False
    
# volume double 倍量
def volume_double(data, i):
    if data['Volume'].iloc[-i-1] < 2.0 * data['Volume'].iloc[-i]:        
        return True
    else:
        return False
    
def get_suffix(stock_symbol):  # represent the region of the stock 
    # Extracts suffix after a dot, if present
    parts = stock_symbol.split('.')
    return parts[-1] if len(parts) > 1 else None

def enough_amount(data, i, stock_symbol):  # positive i
    amount = data['Volume'].iloc[-i] * data['Close'].iloc[-i]
    suffix = get_suffix(stock_symbol)

    # Define different thresholds based on the suffix (different markets)
    threshold = 1e7  # Default threshold for the US market (10 millions usd)
    if suffix == 'T': # Toyko market
        threshold = 1.4e9
    elif suffix == 'L': # london stock
        threshold = 7.8e6
    elif suffix == 'TO': # Toronto stock
        threshold = 1.34e7
    elif suffix == 'SI' : # Singapore Tock exhange
        threshold = 1.34e7
        
    # Check if the turnover > threshold
    if amount > threshold:
        #print(f"{amount} Turnover is enough for {stock_symbol}")
        return True
    else:
        return False

# Initialize lists
breakupList = []
reverseList = []
reboundList = []
breakdownList = []

break_factor = 1.005  # Break factor
begin_ = 3
end_ = 120  # Length of the window

# Iterate through each stock in the list
for i in range(len(stocklist)):
    stock = str(stocklist.iloc[i]["Symbol"])  # Convert stock to string
    print(f"{i+1}/{len(stocklist)} {stock}")

    # Retrieve stock data from Yahoo Finance
    try:
        df = yf.download(stock, start, now)
    except (KeyError, IndexError) as e:
        print(f"Error: {str(e)}")
        continue  # Skip this stock and continue with the next stock if there's an error

    # Check for availability of Low column
    if len(df) < 120:
        print(df)
        continue
    '''
    # Check turnover
    if not enough_amount(df, 2, stock):
        print(f"Turnover too low for {stock}")
        continue  # Skip this stock and continue with the next stock
    '''
    # Pick stocks with low price variation for further processing
    max_h = find_max_high(df, start=2, end=end_)
    min_l = find_min_low(df, start=2, end=end_)
    #print(f"Max. High={max_h}; Min. Low={min_l}")

    processed = False  # Flag to indicate if the stock has been processed

    for length in range(begin_, end_, 1):  # Period of interest, 
        if processed:
            break  # Skip further processing if the stock has been processed

        if upward_wedge(df, start=2, end=length, max_high=max_h):
            
            if green_candle(df, 1) and df['Close'][-1] > break_factor * max_h:  # breakup the upper wedges line
                if stock not in breakupList:
                    breakupList.append(stock) # fake break-out 
                    processed = True  # Mark as processed



       
print(f"{end_} day breakup:")  # Display results
for stock in breakupList:
    print(stock)



