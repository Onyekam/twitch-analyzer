select
    number as number
    , game as game
    , watch_time_mins as watch_time_in_mins
    , stream_time_mins as stream_time_in_mins
    , peak_viewers as peak_viewers
    , peak_channels as peak_channels
    , streamers as streamers
    , average_viewers as average_viewers
    , average_channels as average_channels
    , average_viewer_ratio as average_viewer_ratio
from {{ref('stg__most_watched')}}