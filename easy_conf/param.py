import typing

import yaml

import easy_conf as ec 


class Param:
    """
    Wraps a single config parameter and possible values 
    """

    def __init__(self, key, type, default, required=None, desc=None):
    	# TODO: check if key in config members. If so. Throw error.
        self.key = key
        self.type = type
        self.default = default
        self.required = self.default is ec.REQUIRED if required is None else bool(required)
        self.desc = desc
        self._value = ec.UNSET

    def copy(self):
        return Param(
            key=self.key,
            type=self.type,
            default=self.default,
            required=self.required
        )

    def get_value(self):
        if not self._value is ec.UNSET:
            return self._value
        else:
            return self.default

    def set_value(self, value, check=False):
        if callable(self.type):
            value = self.type(value)
        self._value = value

    def get_serialized(self):
        # TODO: add functionality for custom serialization
        return self.get_value()

    def get_cli_argument(self, hyphenate=False, lowercase=False, prefix=''):
        dest = name = prefix + self.key
        if hyphenate:
            name = name.replace('_', '-')
        if lowercase:
            name = name.lower()
        if isinstance(self.type, typing._GenericAlias):
            type = yaml.safe_load
        else:
            type = self.type
        return name, dict(
            type=type,
            help=self.desc,
            dest=dest,
            default=ec.UNSET,
            required=self.required,
        )

    def __repr__(self):
        return f'Param({self.key} : {self.type} = {self.get_value()})'