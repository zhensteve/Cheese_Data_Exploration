import pandas as pd 
import numpy as np


cheeses = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2024/2024-06-04/cheeses.csv')


pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

cheeses.info()
cheeses.columns
cheeses.shape
cheeses.describe()

cheeses.head(10)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


cheese_subset = cheeses.loc[(~cheeses["milk"].isna()) & (~cheeses['country'].isna()),['cheese', 'milk',
                                                                                       'country', 'region', 'family', 'type',
       'fat_content', 'calcium_content', 'texture', 'rind', 'color', 'flavor',
       'aroma']].copy()


country_cheese_count = cheese_subset["country"]\
                                .value_counts(sort = True, ascending = False) 

multiple_countries = country_cheese_count[country_cheese_count.index.str.contains(',')]

multiple_countries.values.sum() 
''' 
there is 86 incidences where multiple countries came together 
to develop cheeses but for simplicity sake let's focus on cheeses where only one country developed it
'''


single_country_c = cheese_subset.query('~country.isin(@multiple_countries.index)').reset_index(drop = True)

single_country_c.head()

'''
Q1. Top 10 countries that produced cheese?  
    Amongst the top 10 countries - what type of milk is most common?
    What is the preference of texture flavor is most 

Q2. How is the milk associated w/ the flavor and aroma of the cheese color?
    Top 10 milk creatures.  
'''

top_country = single_country_c["country"].value_counts(sort = True, ascending = False).head(10)


top_country_cheese = single_country_c.query('country.isin(@top_country.index)')

top_country_cheese[["primary_milk", "secondary_milk", "tetiary_milk", "last_milk"]] = top_country_cheese['milk'] \
    .str.split(',', expand = True )



cheese_milk_type = top_country_cheese[["cheese", "country", "primary_milk", "secondary_milk", "tetiary_milk", "last_milk"]]\
    .melt(id_vars = ["cheese","country"],  # id variable that we want to keep w/o transposing 
          value_vars = ["primary_milk", "secondary_milk", "tetiary_milk", "last_milk"], # list of variables that we want to transpose, 
          var_name = "order_of_milk", 
          value_name = "milk_type") \
    .query('~milk_type.isna()')

cheese_milk_type["milk_type"] = cheese_milk_type["milk_type"].str.strip()

numerator = cheese_milk_type.groupby(by = ["country", "milk_type"], as_index = False)["cheese"].agg("count") \
                .rename(columns = {'cheese' : 'count'}) # old name:new name
numerator

denominator = top_country_cheese.groupby(by = "country", as_index = False)["cheese"]\
                              .agg({"total":"count"})


cheese_num_denom = pd.merge(left = numerator, right = denominator, how = 'left',
          left_on = 'country', 
          right_on = "country", 
          suffixes = ["d", "n"], 
          indicator = True, 
          validate = "many_to_one") 

cheese_rate = cheese_num_denom.assign(rate = cheese_num_denom["count"] / cheese_num_denom["total"]) \
    .sort_values(by = ['country' , "rate"] , ascending = False)

cheese_rate["rank"] = cheese_rate.groupby("country")["rate"].rank("first", ascending = False)

secondary_cheese = cheese_rate.query("rank == 2").reset_index(drop = True)

print(secondary_cheese)

'''
As expected - most cow milk is the goto product to develop cheese in the top countries. So I pulled the 
the second most popular milk source to develop cheese (amongst the top 10 countries) - turns out goat is secondary goto choice 
to develop milk. (sheep not so much). Surprising - the United Kingdom's second choice of milk source is plant based.
'''

cheese_texture = top_country_cheese[['cheese', 'country', 'texture']]
cheese_texture["country"].unique() # returns a vector or a list of distinct/unique countries

cheese_texture[["first", "second", "third", "fourth", "fifth", "sixth"]] = cheese_texture['texture'].str.split(pat = ", ", expand = True).copy()

cheese_texture["first"] = np.where(cheese_texture["texture"].isna(), "TBA", cheese_texture["first"]) #(condition, if true, else)

cheese_texture_melt = cheese_texture.melt(id_vars = ["cheese", "country"], 
                    value_vars = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth'], 
                    var_name = 'order_of_texture', 
                    value_name = 'texture_type') \
                .query('~texture_type.isna()')

cheese_texture_melt["texture_type"] = cheese_texture_melt["texture_type"].str.strip().copy()


ctm2 = cheese_texture_melt.drop(columns = ["order_of_texture"]).copy()

numerator_texture = ctm2.value_counts(subset = ["country", "texture_type"]).reset_index().rename(columns = {0: "N"})

denominator_texture = ctm2.drop_duplicates(subset = ['country', 'cheese'], keep = 'first') \
                          .value_counts(subset = ["country"])\
                          .reset_index()\
                          .rename(columns = {0:'Denominator'})


texture_join = numerator_texture.merge(denominator_texture,
                        how = 'left', 
                        left_on = "country", 
                        right_on = "country", 
                        suffixes = ['_n', '_d'], 
                        indicator = True,
                        validate = "many_to_one")

texture_join["rate"] = texture_join["N"]/texture_join["Denominator"]

top_three_texture_by_country = texture_join.sort_values(by = ["country", "rate"], ascending = False) \
        .assign(texture_placement = texture_join.groupby(by = ['country'])['rate'].rank(method = 'average', ascending = False)) \
        .query('texture_placement <= 3').reset_index()



import seaborn as sns 
import matplotlib.pyplot as plt
sns.catplot(data = top_three_texture_by_country, x = "texture_type", y = "N", kind = "bar")
plt.show()


texture_join.sort_values(by = ["country", "rate"], ascending = False )

df = sns.load_dataset(data = "penguin")