import redis
from quake_elo import *

redis_conn = redis.Redis(
    'localhost',
    6379,
)

mngr = QuakeEloManager(
    redis_conn,
    'minqlx-plugins:autohandicap:',
    2.,
    .2
)

print(mngr.get_player_merit('111'))

mngr.update([
    dict(
        steam_id='1',
        score=10,
        time=10,
        handicap=100,
    ),
    dict(
        steam_id='2',
        score=5,
        time=9,
        handicap=75,
    ),
])

print(
    mngr.sid_to_merit_to_handicap(
        {
            '1':  10.,
            '2':  80.,
            '3':   5.,
            '4': 500.,
        }
    )
)
