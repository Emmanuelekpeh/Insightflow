#!/bin/bash

case "$1" in
  start)
    sudo service redis-server start
    ;;
  stop)
    sudo service redis-server stop
    ;;
  restart)
    sudo service redis-server restart
    ;;
  status)
    sudo service redis-server status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
