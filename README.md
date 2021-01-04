# Strava Datacollect
This is a small python project which allows you to easily collect your activity data using the offical strava API.

The data is collected and stored to a sqlite Database using the following Datamodel.

Metadata
----
|Table|Column|Datatype|
|---|---|---|
|ACTIVITIES_META|device_name|text|
|ACTIVITIES_META|distance|real|
|ACTIVITIES_META|moving_time|int|
|ACTIVITIES_META|elapsed_time|int|
|ACTIVITIES_META|total_elevation_gain|real|
|ACTIVITIES_META|type|text|
|ACTIVITIES_META|start_date_local|timestamp|
|ACTIVITIES_META|average_speed|real|
|ACTIVITIES_META|max_speed|real|
|ACTIVITIES_META|average_cadence|real|
|ACTIVITIES_META|average_watts|real|
|ACTIVITIES_META|weighted_average_watts|int|
|ACTIVITIES_META|kilojoules|real|
|ACTIVITIES_META|device_watts|int|
|ACTIVITIES_META|has_heartrate|int|
|ACTIVITIES_META|calories|real|
|ACTIVITIES_META|max_watts|int|
|ACTIVITIES_META|gear|text|
|ACTIVITIES_META|id|integer|
|ACTIVITIES_META|last_update|timestamp|

Rawdata
----
|Table|Column|Datatype|
|---|---|---|
|ACTIVITIES_RAW|altitude|real|
|ACTIVITIES_RAW|velocity_smooth|real|
|ACTIVITIES_RAW|cadence|int|
|ACTIVITIES_RAW|grade_smooth|real|
|ACTIVITIES_RAW|heartrate|int|
|ACTIVITIES_RAW|watts|int|
|ACTIVITIES_RAW|distance|real|
|ACTIVITIES_RAW|moving|int|
|ACTIVITIES_RAW|time|int|
|ACTIVITIES_RAW|lat|real|
|ACTIVITIES_RAW|long|real|
|ACTIVITIES_RAW|temp|real|
|ACTIVITIES_RAW|id|int|
|ACTIVITIES_RAW|last_update|timestamp|

Token Info
----
|Table|Column|Datatype|
|---|---|---|
|AUTH_INFO|token_type|text|
|AUTH_INFO|access_token|text|
|AUTH_INFO|refresh_token|text|
|AUTH_INFO|expires_at|text|
|AUTH_INFO|last_update|text|
|AUTH_INFO|user_id|text|


## Requirements
* You have to create a own application to use the strava API. Please follow the [official instructions](http://developers.strava.com/docs/getting-started/) and make sure that you and your usage of this project agree with their ToS and API Agreement.
* In order to use this project I would strongly recommend to use Docker.

## Getting Started
Using the project is very simple with docker. 

1. In the base folder add a _.env_ File with the following content:

CLIENT_ID=_yourclientid(like 123456)_<br>
CLIENT_SECRET=_yourclientsecret(like as1231asdfasd9)_

2. Build the application with <code> docker-compose build </code> from base level
3. Run the application with <code> docker-compose run strava-datacollect </code>

## How it Works
After oauth2 authentication to your application a initialization step is conducted querying all your data from the in the configuration specified years (defaults to 2018, 2019, 2020). This might take several hours as the application does a lot of waiting to not conflict with the API limits. You might want the use less conservative settings changing the configuration parameters.
After initialization it is checked hourly if new data is available from strava. If so it will automatically be added to your Database.

## Further Information
When running the application the first time you need to use oauth2 to provide your application access. Follow the instructions given.

The configuration of the application lives in the config folder. You might want to change things there like the years to collect data from when instantiating the application.

You might not want to use a volume manged by docker (due to accessiablity issues depending on what you are planning to do with your data). Simply changing the strava-database volume to a full path at your local file system should to the job. You can then remove the section in the docker-compose file where the docker volume is defined.

<code> docker-compose up </code> is not working because we lose the stdin needed to get the oauth response url.