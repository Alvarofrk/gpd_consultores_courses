"""
Configuración de Gunicorn para Render.com
Optimizada para evitar timeouts en generación de PDFs
"""

import os

# Configuración básica
bind = "0.0.0.0:10000"
workers = 1
worker_class = "sync"
worker_connections = 1000

# Timeouts optimizados para PDFs
timeout = 120  # 2 minutos para generación de PDFs
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Configuración de memoria
worker_tmp_dir = "/dev/shm"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Configuración de procesos
preload_app = True
reload = False

# Configuración específica para Django
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
