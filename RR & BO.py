import pandas as pd
import numpy as np
import pymc as pm
import math
from tqdm import tqdm
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter('ignore')
import joblib
import random
random.seed(1)
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, KFold, GridSearchCV
from sklearn.metrics import r2_score
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb
from function import encoder, X_y_data
from skopt import gp_minimize, forest_minimize
from skopt.space import Real


#-----------------------------RR fit using Bayesian method-----------------------------#

def bayesian_method(n_initial, x_average, sigma1, sigma2, sigma3, x, y_observed, cores):
    """
    - Parameter:
    ----------- 
            n_initial: Input n value
            x_avergae: Value of cumulative particle size distribution D50
            sigma1: The variance of the n-value
            sigma2: The variance of the De
            sigma3: The variance of the sigma
            x: True cumulative particle size distribution value
            y_observed: Cumulative percent particle size distribution after processing by formula
            cores: The core of the operation

    - Return:
    -----------
            trace: Distribution of values obtained
    
    """

    with pm.Model() as model:
        # define prior distributions for model parameters
        alpha = pm.Normal('alpha', mu= n_initial, sigma= sigma1)
        beta = pm.Normal('beta', mu= x_average, sigma= sigma2)
        sigma = pm.HalfNormal('sigma', sigma= sigma3)

        # define model
        mu = alpha * (np.log(x) - np.log(beta))

        # defining the distribution of observations
        likelihood = pm.Normal('y', mu= mu, sigma= sigma, observed= y_observed)

        # run MCMC sampling
        trace = pm.sample(1000, tune= 50, cores= cores)

    return trace

#-----------------------------define a one-line transformation function-----------------------------#

# define a one-line transformation function
def single_line_change(water_precursor_molratio, pH, temperature, reaction_duration, 
                         dopant_precursor_molratio, additive_precursor_molratio, X, y_De, y_n, index_need):
    """
    - Parameter: 
    -----------
            water_precursor_molratio: The initial molar ratio of water to precursor
            pH: The pH value
            temperature: The temperature in reaction
            reaction_duration: The reaction duration
            dopant_precursor_molratio: The initial molar ratio of precursor to precursor
            additive_precursor_molratio: The initial molar ratio of additive to precursor
            X: The database
            y_De: Corresponding value of De
            y_n: Corresponding value of n
            index_need: Indexes in the dataset you want to change

    - Return:
    -----------
            X_test_select_De: Changed De
            X_test_select_n: Changed n
    
    """
    X.loc[index_need, 'Water_precursor_molratio'] = water_precursor_molratio
    X.loc[index_need, 'pH'] = pH
    X.loc[index_need, 'Temperature(℃)'] = temperature
    X.loc[index_need, 'Reaction_duration(h)'] = reaction_duration
    X.loc[index_need, 'Solvent_species'] = 'solvent'
    X.loc[index_need, 'Solution_precursor_molratio'] = water_precursor_molratio
    X.loc[index_need, 'Dopant_species'] = 'dopant'
    X.loc[index_need, 'Dopant_precursor_molratio'] = dopant_precursor_molratio
    X.loc[index_need, 'Additive_species'] = 'additive'
    X.loc[index_need, 'Additive_precursor_molratio'] = additive_precursor_molratio

    #De
    X_select_De = encoder(X, y_De, 'Precursor_species', 'LeaveOneOutEncooder')
    X_select_De = encoder(X_select_De, y_De, 'Additive_species', 'LeaveOneOutEncooder')
    X_select_De = encoder(X_select_De, y_De, 'Dopant_species', 'LeaveOneOutEncooder')
    X_select_De = encoder(X_select_De, y_De, 'Solution_species', 'LeaveOneOutEncooder')
    X_select_De = encoder(X_select_De, y_De, 'Stir', 'OneHotEncoder')
    scaler = StandardScaler()
    X_select_De = scaler.fit_transform(X_select_De)
    X_select_De = pd.DataFrame(X_select_De)

    #n
    X_select_n = encoder(X, y_n, 'Precursor_species', 'LeaveOneOutEncooder')
    X_select_n = encoder(X_select_n, y_n, 'Additive_species', 'LeaveOneOutEncooder')
    X_select_n = encoder(X_select_n, y_n, 'Dopant_species', 'LeaveOneOutEncooder')
    X_select_n = encoder(X_select_n, y_n, 'Solution_species', 'LeaveOneOutEncooder')
    X_select_n = encoder(X_select_n, y_n, 'Stir', 'OneHotEncoder')
    scaler = StandardScaler()
    X_select_n = scaler.fit_transform(X_select_n)
    X_select_n = pd.DataFrame(X_select_n)

    X_test_select_De = X_select_De.loc[X.index.get_loc(index_need), :]
    X_test_select_n = X_select_n.loc[X.index.get_loc(index_need), :]

    return X_test_select_De, X_test_select_n

#-----------------------------sythesis parameter reverse design platform-----------------------------#

# define the objective function
def objective_function(params, de_model, n_model, X, y_De, y_n, de_target):
    """
    - Parameter:
    -----------
            (params)
            water_precursor_molratio: The initial molar ratio of water to precursor
            pH: The pH value
            temperature: The temperature in reaction
            reaction_duration: The reaction duration
            dopant_precursor_molratio: The initial molar ratio of precursor to precursor
            additive_precursor_molratio: The initial molar ratio of additive to precursor

            X: The database
            y_De: Corresponding value of De
            y_n: Corresponding value of n
            de_model: De model
            n_model: n model
            de_target: Target De

    - Return:
    -----------
            E_de[0]: The relative error of De
    
    """
    water_precursor_molratio, pH, temperature, reaction_duration, dopant_precursor_molratio, additive_precursor_molratio = params
    X_test_de, X_test_n = single_line_change(water_precursor_molratio, pH, temperature, reaction_duration, 
                                    dopant_precursor_molratio, additive_precursor_molratio, 
                                    X, y_De, y_n)
    de_new = de_model.predict(X_test_de.values.reshape(1, -1))
    n_new = n_model.predict(X_test_n.values.reshape(1, -1))
    de_target = 'target'
    E_de = abs((de_new - de_target) / de_target)

    return E_de[0]

# 
def platform(params, de_model, n_model, X, y_De, y_n, de_target):
    """
    - Parameter:
    -----------
            (params)
            water_precursor_molratio: The initial molar ratio of water to precursor
            pH: The pH value
            temperature: The temperature in reaction
            reaction_duration: The reaction duration
            dopant_precursor_molratio: The initial molar ratio of precursor to precursor
            additive_precursor_molratio: The initial molar ratio of additive to precursor
            
            X: The database
            y_De: Corresponding value of De
            y_n: Corresponding value of n
            de_model: De model
            n_model: n model
            de_target: Target De

    - Return:
    -----------
            optimized_solution: Optimized formulation parameters
            optimized_de: Optimized de
            optimized_n: Optimized n
    
    """
    # define parameter spaces
    space = [
        Real(1, 40, name='water_precursor_molratio'),
        Real(1, 4.5, name='pH'),
        Real(90, 100, name='temperature'),
        Real(1, 24, name='reaction_duration'),
        Real(0.01, 0.2, name='dopant_precursor_molratio'),
        Real(0.0003, 0.1, name='additive_precursor_molratio')
    ]

    # run BO
    x0 = [18.2, 1.8, 100, 22, 0.1, 0.04]
    result = gp_minimize(objective_function(params, de_model, n_model, X, y_De, y_n, de_target), space, n_calls=40, x0=x0, random_state=1)

    # ouput results
    optimized_solution = result.x
    optimized_de = de_model.predict(single_line_change(*optimized_solution, X, y_De, y_n)[0].values.reshape(1, -1))
    optimized_n = n_model.predict(single_line_change(*optimized_solution, X, y_De, y_n)[1].values.reshape(1, -1))

    return optimized_solution, optimized_de, optimized_n