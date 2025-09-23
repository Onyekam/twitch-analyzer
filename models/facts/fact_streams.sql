with streams as (
    select
        *
    from {{ref('tmp_streams')}} 
)

, with_game_data as (
    select
        rs.sk_stream_id as sk_stream
        , rs.user_id
        , rs.user_login
        , rs.created_dt
        , rs.game_name as stream_game_name
        , g.sk_game
        , g.game_name
    from streams rs
    left join {{ref('games')}} g on rs.game_name = g.game_name    
)
select 
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts 
from with_game_data

