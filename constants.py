class MQTopicTypes:
  HEARTBEAT = "hb"  
  COMMAND = "cmd"

def enum_set(c):
  return set(
    value for key, value in c.__dict__.items() if not key.startswith('__')
  )
