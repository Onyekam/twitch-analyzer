with prep as (
    select distinct
    g.id
    , g.name
    , g.genres
    , g.platforms
    , g.summary
    from {{ source('twitchdata','source_igdb_prod')}} g
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from prep