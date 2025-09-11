with users as (
    select distinct
        lower(user_login) as login
        , user_id
        , {{hash(['user_login', 'user_id'])}} as sk_games
    from {{ref('tmp_streams')}}
)
select
    *
    , current_date as tch_created_ts
    , current_date as tch_updated_ts
from users
