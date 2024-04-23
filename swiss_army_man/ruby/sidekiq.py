import json
import uuid
from .. import RedisCache

class Sidekiq():
    @classmethod
    def redis(cls):
        if not hasattr(cls, '_redis_cache'):
            cls._redis_cache = RedisCache()
        return cls._redis_cache


    # job = {
    #     'class': 'MyWorker',
    #     'args': ['arg1', 'arg2'],
    #     'retry': True,
    #     'queue': 'default'
    # }
    @classmethod
    def enqueue(cls, job):
        job = {**job, "queue": "default", "retry": True}
        # job['jid'] = str(uuid.uuid4())  # Generate a unique job ID
        job_json = json.dumps(job)
        queue_name = f"queue:{job['queue']}"
        return cls.redis().lpush(queue_name, job_json)
