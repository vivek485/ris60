
#best
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pytz
from datetime import datetime, timedelta
from datetime import date
import numpy as np
import ta
import asyncio
import aiohttp
import nest_asyncio
#from allstocks import symbols
from variable import s



buystock = []
sellstock = []

interval = 5 # enter 15,60,240,1440,10080,43800
dayback = 15
ed = datetime.now()
stdate = ed - timedelta(dayback)

st.set_page_config(layout="wide")
st.title('Stock Trading RSI 60 crossing')
day_to_getdata = st.number_input(label='Daysback',min_value=-10,max_value=0,value=-1)
st.write('Enter the number of days to get data in -1,-2 ,-3')


def conv(x):

    timestamp = int(x.timestamp() * 1000)
    timestamp_str = str(timestamp)[:-4] + '0000'
    final_timestamp = int(timestamp_str)
    return  final_timestamp

ist_timezone = pytz.timezone('Asia/Kolkata')

fromdate = conv(stdate)
todate = conv(ed)




async def getdata(session, stock):


    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        #'Accept-Encoding': 'gzip, deflate, br'
    }
    url = f'https://groww.in/v1/api/charting_service/v2/chart/exchange/NSE/segment/CASH/{stock}?endTimeInMillis={todate}&intervalInMinutes={interval}&startTimeInMillis={fromdate}'
    async with session.get(url, headers=headers) as response:
        try:
            
            resp = await response.json()
            candle = resp['candles']
            dt = pd.DataFrame(candle)
            fd = dt.rename(columns={0: 'datetime', 1: 'Open', 2: 'High', 3: 'Low', 4: 'Close', 5: 'Volume'})
            
            
            fd['symbol'] = stock
            pd.options.mode.chained_assignment = None
            final_df = fd
            

            final_df['Open'] = final_df['Open'].astype(float)
            final_df['Close'] = final_df['Close'].astype(float)
            final_df['High'] = final_df['High'].astype(float)
            final_df['Low'] = final_df['Low'].astype(float)
            final_df['Volume'] = final_df['Volume'].astype(float)
            final_df['datetime1'] = pd.to_datetime(final_df['datetime'], unit='s', utc=True)
            final_df['datetime1'] = final_df['datetime1'].dt.tz_convert(ist_timezone)
            
            

# Format the datetime to 'dd:mm:yyyy hh:mm:ss'
            #final_df['datetime1'] = final_df['datetime1'].dt.strftime('%d:%m:%Y %H:%M:%S')

            final_df.set_index(final_df.datetime1, inplace=True)
            final_df.drop(columns=['datetime'], inplace=True)

            final_df['prevopen'] = final_df['Open'].shift(1)
            final_df['prevhigh'] = final_df['High'].shift(1)
            final_df['prevlow1'] = final_df['Low'].shift(2)
            final_df['prevhigh1'] = final_df['High'].shift(2)
            final_df['prevlow2'] = final_df['Low'].shift(3)
            final_df['prevhigh2'] = final_df['High'].shift(3)
            final_df['prevclose'] = final_df['Close'].shift(1)
            
            
        
            final_df['time_column'] = final_df.datetime1.dt.time
            
            time_string = "09:15:00"            
#----------------------
            final_df['rsi'] = round(ta.momentum.rsi(close=final_df['Close'], window=14))
            final_df['prevrsi'] = final_df['rsi'].shift(1)
            final_df['ma200'] = round(ta.momentum._ema(series=final_df['Close'],periods=200))
            
            newdf = final_df
            
            newdf['rsibreakup'] = np.where(((newdf['prevrsi'] <60) & (newdf['rsi'] > 60 )),1,0)
            newdf['rsibreakdown'] = np.where(((newdf['prevrsi'] > 40) & (newdf['rsi'] < 40 )),1,0)

            newdf = newdf.iloc[-100:]
           
            newdf1 = final_df[final_df.index.time == pd.to_datetime(time_string).time()].reset_index(drop=True)
            
            last_candle = newdf1.iloc[day_to_getdata]
            
            
            
            if last_candle['rsibreakdown'] == 1:#2
                sellstock.append(last_candle['symbol'])
                #st.write(last_candle['symbol'])

                

                fig = go.Figure(data=[go.Candlestick(x=newdf.index, open=newdf.Open, close=newdf.Close, high=newdf.High,low=newdf.Low,name=stock),
                                      go.Scatter(x=newdf.index, y=newdf.ma200, line=dict(color='red', width=2),name='ma200')
                                      ])
                # fig.add_trace(
                #     go.Scatter(x=newdf[newdf['o-hs']==1].index, y=newdf[newdf['o-hs']==1]['High'], mode='markers', marker_symbol='triangle-down',
                #                marker_size=25,marker_color='red'))
               

                fig.update_layout(autosize=False, width=1800, height=800, xaxis_rangeslider_visible=False)
                fig.layout.xaxis.type = 'category'
                
                st.write(' rsi sell stratergy')
                st.plotly_chart(fig)

            if last_candle['rsibreakup'] == 1:#3

                buystock.append(last_candle['symbol'])
                fig = go.Figure(data=[go.Candlestick(x=newdf.index, open=newdf.Open, close=newdf.Close, high=newdf.High,low=newdf.Low,name=stock),                                     
                                      go.Scatter(x=newdf.index, y=newdf.ma200, line=dict(color='blue', width=2),name='ma200')])
                # fig.add_trace(
                #     go.Scatter(x=newdf[newdf['o-ls']==1].index, y=newdf[newdf['o-ls']==1]['Low'], mode='markers', marker_symbol='triangle-up',
                #                marker_size=25,marker_color='green'))
                

                fig.update_layout(autosize=False, width=1800, height=800, xaxis_rangeslider_visible=False)
                fig.layout.xaxis.type = 'category'
                
                st.write(' rsi buy stratergy')
                st.plotly_chart(fig)



            return
        except:
            print('no data')
            pass


async def main():
    async with aiohttp.ClientSession() as session:

        tasks = []
        for stocks in s:
            try:
                stock = stocks

                task = asyncio.ensure_future(getdata(session, stock))

                tasks.append(task)
            except:
                pass
        df = await asyncio.gather(*tasks)
        # print(df)


nest_asyncio.apply()
asyncio.run(main())





st.write('buy')
st.write(buystock)
st.write('sell')
st.write(sellstock)

