select
distinct game_name
, game_id as sk_game
from {{ref('stg_new_source_september_prod')}}
where game_name !=  ""