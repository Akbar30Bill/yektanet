create table short_url(
  short_url_uuid uuid,
  url   text,
  shorted_url text,
  creator_uuid uuid,
  is_pref_short boolean default false,
  create_timestamp timestamp default now()
);
create table users(
  user_uuid uuid,
  username text unique,
  password text,
  email text
);
create table url_query(
  user_uuid uuid,
  short_url_uuid uuid,
  create_timestamp timestamp default now(),
  user_agent text
);
create index findurl_index_with_pref on short_url(shorted_url, is_pref_short);
create index findurl_index on short_url(shorted_url);
create index user_pass on users(username, password);
