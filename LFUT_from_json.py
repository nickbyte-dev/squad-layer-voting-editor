# %%
# --- Importing packages --- #

import pandas as pd
import numpy as np
import json

# %%
# --- Importing JSON file --- #

with open('layers.json') as json_file:
    data = json.load(json_file)

# %%
# --- Hardcoded variables --- #

    # List of columns needed for the layers_info and factions_info df
layer_columns = ['levelName', 'gamemode', 'mapName', 'factions']
faction_columns = ['unitObjectName', 'factionID', 'alliance']

    # List of gamemodes that need to be filtered out of layers_info df
filter_gamemode = ['Seed', 'Training', 'Tutorial', 'Lobby', 'Fireteam']
    # List of factions that need to be filtered out of factions_info df
filter_faction = ['CIV']
    # List of substrings that need to be filtered out of factions_info df
filter_unit = ['Skirmish', 'Seed', 'FS', 'Tutorial']
filter_unit = '|'.join(filter_unit)

    # List of colors for the alliances
alliance_colors = ["Blues", "Greens", "Oranges", "Reds"]

# %%
# --- df and variable functions --- #

# Function to create the main dfs: layers_info and factions_info
def create_info_df_JSON(data:dict, columns:list, filter:list, key:str):

    if key == 'Maps':
        info_df = pd.DataFrame(data[key])[columns] # Get correct columns from data
        info_df = info_df[~info_df[columns[1]].isin(filter)] # Filter out gamemodes
    elif key == 'Units':
        info_df = pd.DataFrame(data[key]).T[columns] # Get correct columns from data
        info_df = info_df[~info_df[columns[1]].isin(filter_faction)] # Filter out CIV faction
        info_df = info_df[~info_df[columns[0]].str.contains(filter, na=False)]
        info_df[columns[0]] = info_df[columns[0]].str.split("_").str[-1]
    else:
        #TODO add custom error message
        a = 1

    return info_df

# Function to create variables from the layers_info df
def create_layer_variables_JSON(info_df:pd.DataFrame, columns:list):

    Layers = sorted(info_df[columns[0]].unique().tolist())
    GameModes = sorted(info_df[columns[1]].unique().tolist())
    Levels = sorted(info_df[columns[2]].unique().tolist())

    return Levels, GameModes, Layers

# Function to create variables from the factions_info df
def create_faction_variables_JSON(info_df:pd.DataFrame, columns:list):

    Teams = ['1', '2']
    Units = sorted(info_df[columns[0]].unique().tolist())
    Alliances = (info_df.groupby(columns[2])[columns[1]].unique().apply(lambda x: sorted(x)).to_dict())
    Factions = [item for values in Alliances.values() for item in values]
    Faction_Unit_Team_All = [f"{x}_{y}_{z}" for z in Teams for x in Factions for y in Units]

    return Alliances, Factions, Units, Teams, Faction_Unit_Team_All

# Function to create LFUT dictionary entries (layer = key, FUT_list = value)
def FUT_dictionary_JSON(info_s:pd.Series, unit_list:list, columns:list):
    FUT_list = []

    layer = info_s[columns[0]]
    FUT_info = info_s[columns[3]]
    keys = list(FUT_info[0].keys())

    for i in range(len(FUT_info)):

        faction = FUT_info[i][keys[0]]
        default_unit = FUT_info[i][keys[1]].split("_")[-1]
        default_unit = default_unit if default_unit in unit_list else unit_list[3]
        teams = FUT_info[i][keys[2]]
        units = FUT_info[i][keys[3]]

        for team in teams:
            FUT_list.append(f"{faction}_{default_unit}_{team}")

        for unit in units:
            for team in teams:
                FUT_list.append(f"{faction}_{unit}_{team}")

    return layer, FUT_list

# Function to create LFUT df
def LFUT_JSON(info_df:pd.DataFrame, LFUT_empty:pd.DataFrame, columns:list, units:list):

    LFUT_df = LFUT_empty.copy()

    # Creating LFUT dict
    LFUT_dict = {}
    for i in range(len(info_df[columns[0]])):
        layer, FUT_list = FUT_dictionary_JSON(info_df.iloc[i], units, columns)
        LFUT_dict[layer] = FUT_list

    # Filling empty LFUT df with false values if LFUT combinations that exist
    for layer, FUTs in LFUT_dict.items():
        column = [fut for fut in FUTs if fut in LFUT_df.columns]
        LFUT_df.loc[layer, column] = False

    # Create the LFUT_df
    LFUT_df = LFUT_df.dropna(axis=1, how="all")

    # Add layer exclusion column
    LFUT_df.insert(loc=0, column='Exclude', value=False)

    return LFUT_df

# %%
# --- Info dfs --- #

layers_info = create_info_df_JSON(data, layer_columns, filter_gamemode, "Maps")
factions_info = create_info_df_JSON(data, faction_columns, filter_unit, "Units")

# %%
# --- Variables --- #

Levels, GameModes, Layers = create_layer_variables_JSON(layers_info, layer_columns)
Alliances, Factions, Units, Teams, Faction_Unit_Team_All = create_faction_variables_JSON(factions_info, faction_columns)

# %%
# --- LFUT --- #
LFUT_empty = pd.DataFrame(index=Layers, columns=Faction_Unit_Team_All)
LFUT_df = LFUT_JSON(layers_info, LFUT_empty, layer_columns, Units)
Faction_Unit_Team = LFUT_df.columns.tolist()
LFUT_df.to_csv('LFUT.csv')
