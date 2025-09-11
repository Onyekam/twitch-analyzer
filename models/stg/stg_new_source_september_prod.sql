select
  *
 from {{ source('twitchdata','new_source_september_prod')}}