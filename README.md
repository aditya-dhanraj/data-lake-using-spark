# Project: Data Lake

## Introduction
This project aims to create analytical parquet tables on Amazon S3 using AWS ElasticMapReduce/Spark to extract, load and transform songs data and event logs from the usage of the Sparkify app.

From this tables we will be able to find insights in what songs their users are listening to.

## Getting started

To run this project in local mode, create a file dl.cfg in the root of this project with the following data:

    KEY=YOUR_AWS_ACCESS_KEY
    SECRET=YOUR_AWS_SECRET_KEY
Create an S3 Bucket named sparkify-dend where output results will be stored.

Finally, run the following command:

    python etl.py

To run on an Jupyter Notebook powered by an EMR cluster, import the notebook found in this project.

## Data sources
We will read basically two main data sources:

> s3a://udacity-dend/song_data/*/*/* - JSON files containing meta information about song/artists data
> s3a://udacity-dend/log_data/*/* - JSON files containing log events from the Sparkify app

## Parquet data schema
After reading from these two data sources, we will transform it to the schema described below:

**Fact Table**

*songplays* - records in event data associated with song plays i.e. records with page NextSong songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent

**Dimension Tables**

**users** - users in the app user_id, first_name, last_name, gender, level

**songs** - songs in music database song_id, title, artist_id, year, duration

**artists** - artists in music database artist_id, name, location, lattitude, longitude

**time** - timestamps of records in songplays broken down into specific units start_time, hour, day, week, month, year, weekday


