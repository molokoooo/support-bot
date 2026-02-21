from redis.asyncio import Redis

r_session = Redis(host="localhost", port=6379, db=0, decode_responses=True)

"""
Keys:
r_session.hset(f"user_admin:{id}", mapping={role})
r_session.hset(f"faq:{id}", maping={})

"""
