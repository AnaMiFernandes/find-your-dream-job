#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 11:26:28 2021

@author: vlud

Structuring the entire data pipeline. 

1. IndeedScraper scrapes Indeed jobs and saves them as JSON. 

2. IndeedProcessor: 
    Loads JSON files and Kaggle dataset
    Removes duplicates with naive solution
    Assembles them into a single dataframe and exports it as joblib
    
3. Database loads the joblib, saves the jobs into database (if they are not there already).
   It can export the whole database as a dataframe. 
   
4. CleanDuplicates accesses the Database and removes duplicates according to 
   doc2vec solution. 

"""

import os
import fydjob
from fydjob.NLPFrame import NLPFrame
from fydjob.IndeedProcessor import IndeedProcessor
from fydjob.Database import Database
from fydjob.Doc2VecPipeline import Doc2VecPipeline
from fydjob.Word2VecPipeline import Word2VecPipeline


home_path = os.path.dirname(fydjob.__file__) 


class Pipeline:
    
     def __init__(self):
         #this does not seem to work
         output_folder = os.path.join(home_path, 'output')
         if not os.path.exists(output_folder):
             os.mkdir(output_folder)
         
     def long_pipeline(self):
         '''Performs the full pipeline (see readme).'''
         #Process Indeed scrapings and Kaggle data.
         ip = IndeedProcessor()
         ip.pipe()
         ip.export()
         
         #create and populate database
         db = Database()
         db.create_tables()
         db.populate(limit=None)
         
         #load dataframe from database 
         ndf = NLPFrame() 
         
         #similarity sweep
         ndf.get_duplicates()
         db.remove_sims_duplicates()
         ndf.reset_data()
         
         #add NLP fields
         ndf.add_token_fields()
         ndf.process_text()
         
     def short_pipeline(self, limit=None):
        '''Short pipeline starting from database (see readme).'''
        ndf = NLPFrame()
        ndf.add_token_fields()
        ndf.process_text()
        ndf.add_skills() 
        
        print('Preprocessing complete.')
        print("Columns and NaN values:")
        print(ndf.df.isna().sum())
        
        if limit: 
            df = ndf.df[:limit]
        else:
            df = ndf.df
        
        print('Instantiating models...')
        wp = Word2VecPipeline(df)
        dp = Doc2VecPipeline(df)
        
        print("Testing models")
        
        skill = 'python'
        print(f'Most similar skills to {skill}:')
        print(wp.most_similar('python'))
        
        print("Most similar jobs:")
        job_text = ndf.df.job_text_tokenized.iloc[0]
        print(dp.find_similar_jobs(job_text, 1))
        