# from kombu import Queue
# from kombu import Exchange

broker_url = "pyamqp://svensson:olof@linsvensson"

result_backend = "redis://linsvensson:6379/2"

# broker_transport_options = {
#     'queue_order_strategy': 'priority',
# }

# timezone = 'UTC'
# enable_utc = True
#
# default_queue = "scheduled"
# queues = (
#     Queue("scheduled", Exchange("scheduled"), routing_key="shed"),
#     Queue("proactive_monitoring", Exchange("proactive_monitoring"), routing_key="prmon"),
#
# )