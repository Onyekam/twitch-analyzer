with prep as (
    select
        sg.sk_game
        , ig.game_name
        , ig.genres
        , ig.platforms
        , ig.summary
        , ig.image
    from {{ref('tmp_games')}} sg -- as stream games
    inner join {{ref('tmp_igdb_games')}} ig on sg.game_name = ig.game_name
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from prep