import configparser
from datetime import datetime
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format
from pyspark.sql.functions import monotonically_increasing_id
from pyspark.sql import functions as F
from pyspark.sql.types import *

#connect to aws and access s3 bucket

config = configparser.ConfigParser()
config.read('dl.cfg')

os.environ['AWS_ACCESS_KEY_ID']=config['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY']=config['AWS_SECRET_ACCESS_KEY']


def create_spark_session():
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
        .getOrCreate()
    return spark


def process_song_data(spark, input_data, output_data):
    """
        Description: This function loads song_data from S3 and processes it by extracting the songs and artist tables
        and then again loaded back to S3 in parquet format
        
        Parameters:
            spark       : Spark Session
            input_data  : location of song_data json files with the songs metadata
            output_data : S3 bucket were dimensional tables in parquet format will be stored
    """
    # get filepath to song data file
    song_data = input_data + 'song_data/*/*/*/*.json'
    
    """ Defined Schema for song_data"""
    
    songSchema = StructType([
        StructField("artist_id", StringType()),
        StructField("artist_latitude", DoubleType()),
        StructField("artist_location", StringType()),
        StructField("artist_longitude", DoubleType()),
        StructField("artist_name", StringType()),
        StructField("duration", DoubleType()),
        StructField("num_songs", IntegerType()),
        StructField("song_id", StringType()),
        StructField("title", StringType()),
        StructField("year", IntegerType())  
    ])
    
    # read song data file
    df = spark.read.json(song_data, schema=songSchema)

    # extract columns to create songs table
    songs_field = ["song_id", "title", "artist_id", "year", "duration"]
    songs_table =  df.select(songs_field).dropDuplicates()
    
    # write songs table to parquet files partitioned by year and artist
    songs_table.write.partitionBy("year", "artist_id").parquet(output_data + 'song/' , mode="overwrite")

    # extract columns to create artists table
    artists_field = ["artist_id","artist_name as name", "artist_location as location", "artist_latitude as latitude", "artist_longitude as longitude"]
    artists_table = df.selectExpr(artists_field).dropDuplicates()
    
    # write artists table to parquet files
    artists_table.write.parquet(output_data + 'artist/', mode="overwrite")


def process_log_data(spark, input_data, output_data):
    """
        Description: This function loads log_data from S3 and processes it by extracting the users and time table
        and then again loaded back to S3. Also output from previous function is used in by spark.read.json command
        
        Parameters:
            spark       : Spark Session
            input_data  : location of log_data json files with the events data
            output_data : S3 bucket were dimensional tables in parquet format will be stored
            
    """
    # get filepath to log data file
    log_data = input_data + 'log_data/*.json'

    # read log data file
    df = spark.read.json(log_data)
    
    # filter by actions for song plays
    df = df.filter(df.page == 'NextSong')

    # extract columns for users table    
    users_field = ["userId as user_id ", "firstName as first_name", "lastName as last_name", \
                   "gender", "level"]
    users_table = df.selectExpr(users_field).dropDuplicates()
    
    # write users table to parquet files
    users_table.write.parquet(output_data + 'user/', mode="overwrite")


    # create timestamp column from original timestamp column
    def date_convert(ts):
        return datetime.fromtimestamp(ts / 1000.0)
             
    get_datetime = udf(date_convert, TimestampType())
    df = df.withColumn("start_time", get_datetime('ts'))
     
    # extract columns to create time table
    time_table = df.select("start_time").dropDuplicates()                  \
                .withColumn("hour",    hour(col("start_time")))            \
                .withColumn("day",     date_format(col("start_time"),"d")) \
                .withColumn("week",    date_format(col("start_time"),"w")) \
                .withColumn("month",   month(col("start_time")))           \
                .withColumn("year",    year(col("start_time")))            \
                .withColumn("weekday", date_format(col("start_time"), "EEEE"))
    
    # write time table to parquet files partitioned by year and month
    time_table.write.partitionBy("year", "month").parquet(output_data + 'time/', mode="overwrite")

    # read in song data to use for songplays table
    song_df = spark.read.parquet(output_data + 'song/')

    # extract columns from joined song and log datasets to create songplays table 
    songplays_table = (
        df.withColumn("songplay_id", F.monotonically_increasing_id())
          .join(song_df, song_df.title == df.song)
          .select(
            "songplay_id",
            col("start_time"),
            col("userId").alias("user_id"),
            "level",
            "song_id",
            "artist_id",
            col("sessionId").alias("session_id"),
            "location",
            col("userAgent").alias("user_agent")
          )
    )
   

    # write songplays table to parquet files partitioned by year and month
    songplays_table.write.parquet(output_data + "songplays/", mode="overwrite")


def main():
    """
        Extract songs and events data from S3, Transform it into dimensional tables format, and Load it back to S3 in Parquet format
    """
    spark = create_spark_session()
    input_data = "s3a://udacity-dend/"
    output_data = "s3a://spark-dend/"
    
    process_song_data(spark, input_data, output_data)    
    process_log_data(spark, input_data, output_data)


if __name__ == "__main__":
    main()
