with games as (
    select
    distinct lower(game_name) as game_name
    , game_id
    , {{hash(['game_name', 'game_id'])}} as sk_game
    from {{ref('tmp_streams')}}
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from games
