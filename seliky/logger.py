import sys
import os
import time
from loguru import logger as log


# 日志设置
log.configure(handlers=[{
    'sink': sys.stderr,
    'format': '<green>{time:YYYY-MM-DD HH:mm:ss}</> <cyan>{file}</><lvl>{line:4} <level>| {level} {message}</level></>',
    'colorize': True
}])
log.add(sink=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Outputs",
                          'logs') + os.sep + time.strftime("%Y-%m-%d %H%M", time.localtime()) + '.log',
        level='TRACE',
        format="{time:YYYY-MM-DD HH:mm:ss} {file} {message}",
        colorize=False,
        encoding='utf-8')
