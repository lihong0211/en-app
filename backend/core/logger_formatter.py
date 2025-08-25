import logging

from flask import g


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = getattr(g, 'trace_id', None)
        return True


class TraceLoggerFormatter(logging.Formatter):
    def format(self, record):
        record.trace_id = getattr(record, 'trace_id', 'N/A')
        return super().format(record)
