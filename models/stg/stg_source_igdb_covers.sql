with prep as (
    select distinct
        id
        , game
        , url
    from {{ source('twitchdata','source_igdb_covers_prod')}}
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from prep
