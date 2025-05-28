select
    _number_ as number
    , * except(_number_)
 from {{ source('twitchdata','most_watched')}}