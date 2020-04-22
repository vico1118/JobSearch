import redis
redis_cli = redis.StrictRedis(host='localhost', port=6379)
redis_cli.incr('test_count')