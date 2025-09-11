select
    count(*) as times_played
    , lower(game_name) as game_name
    , created_dt
from {{ref('fact_streams')}}
group by all
order by times_played desc