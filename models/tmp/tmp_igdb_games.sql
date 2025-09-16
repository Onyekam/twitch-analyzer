with prep as (
    select
        g.id
        , lower(g.name) as game_name
        , g.genres
        , g.platforms
        , g.summary
        , concat('https:',c.url) as image
    from {{ref('stg_source_igdb_games')}} g
    inner join  {{ref('stg_source_igdb_covers')}} c on g.id = c.game
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from prep