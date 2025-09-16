with raw_streams as (
    select distinct
      {{hash(['user_id', 'game_id', 'date(created_ts)'])}} as sk_stream_id
      , user_id
      , user_login
      , game_name
      , game_id
      , date(created_ts) as created_dt
      --, created_ts as tch_created_ts
    from {{ source('twitchdata','new_source_september_prod')}}
    where 1 = 1 
    and game_name != ""
    and game_name not in (
      "0 = 0 = 0"
        , "#BLUD"
        , "testinggame"
        , "|][-@I7 in vitro #Dead in Vitro"
        , "term.ooo"
        , "b"
        , "YEAH! YOU WANT \"THOSE GAMES,\" RIGHT? SO HERE YOU GO! NOW, LET'S SEE YOU CLEAR THEM!"
        , "X遊戲"
        , "Unknown"
    )
    and (
        game_name not like ".%"
        and game_name not like "00000%"
    )

    and (
        user_name not in (
            ""
        )
        or user_id is not null
    )
)
, with_game_data as (
    select
        rs.sk_stream_id as sk_stream
        , rs.user_id
        , rs.user_login
        , rs.created_dt
        , g.*
    from raw_streams rs
    left join {{ref('games')}} g on rs.game_name = g.game_name    
)
select
    *
from with_game_data
