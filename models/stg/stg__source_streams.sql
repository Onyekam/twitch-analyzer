select
  *
 from {{ source('twitchdata','source_streams')}}