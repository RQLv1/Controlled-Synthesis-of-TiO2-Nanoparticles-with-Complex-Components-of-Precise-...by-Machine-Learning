#-----------------------------data input and output----------------------------------------------#
def  X_y_data(file_path):
    
    """
    - Parameters:
    -----------
    file_path: the excel dataset 

    - Renturn:
    -----------
    X,y: are the ml inputs
    """
    import pandas as pd
    import numpy as np

    df = pd.read_excel(file_path)
    X = df.iloc[:, :12]
    columns_name = ['D3(nm)', 'D10(nm)', 'D25(nm)', 'D50(nm)', 'D75(nm)','D90(nm)', 'D99(nm)','Average(nm)',]
    y = df[columns_name]  

    return X, y  

#-----------------------------encode----------------------------------------------#
def encoder(X, y_single, column_name, encode_scheme):
    """
    Parameters:
    -----------
    X: feature data
    y_single: label data for one column
    column_name: the column need to encode
    encode_scheme: the encode scheme

    Renturn:
    -----------
    X_new: the new feature data after encoding
    """
    from category_encoders import LeaveOneOutEncoder
    from category_encoders import OneHotEncoder
    
    if encode_scheme == 'LeaveOneOutEncoder':

        enc_leaveoneout = LeaveOneOutEncoder(cols= column_name)
        X_new = enc_leaveoneout.fit_transform(X, y_single)
    
    if encode_scheme == 'OneHotEncoder':
        enc_onehot = OneHotEncoder(cols= column_name)
        X_new = enc_onehot.fit_transform(X, y_single)

    return X_new
