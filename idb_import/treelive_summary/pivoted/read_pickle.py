import pandas as pd

df = pd.DataFrame.load("dfpiv.pickle")

sel = df[ 
    (df['TPA_Douglas-fir_10'] > 0) &
    (df['TPA_Douglas-fir_14'] > 0) &
    (df['TPA_Red alder_6'] > 0) 
]

