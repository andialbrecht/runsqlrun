def get_backend(config):
    if config.get('driver', None) == 'psql':
        from rsr.connections.backends import psql
        return psql.Driver(config)
    else:
        raise NotImplementedError()
