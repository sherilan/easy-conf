import argparse 
import collections 
import contextlib 
import inspect 
import os 
import typing 
import warnings 

import yaml 

REQUIRED = object()
UNSET = object()

class Param:
    """
    Wraps a single config parameter and possible values 
    """

    def __init__(self, key, type, default, required=None, desc=None):
        # TODO: check if key in config members. If so. Throw error.
        self.key = key
        self.type = type
        self.default = default
        self.required = self.default is REQUIRED if required is None else bool(required)
        self.desc = desc
        self._value = UNSET

    def copy(self):
        return Param(
            key=self.key,
            type=self.type,
            default=self.default,
            required=self.required
        )

    def get_value(self):
        if not self._value is UNSET:
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
        elif issubclass(self.type, (list, tuple)):
            type = yaml.safe_load 
        else:
            type = self.type
        return name, dict(
            type=type,
            help=self.desc,
            dest=dest,
            default=UNSET,
            required=self.required,
        )

    def __repr__(self):
        return f'Param({self.key} : {self.type} = {self.get_value()})'

class Config(collections.OrderedDict):
    """
    Base class for config objects 
    """

    def __init__(self, values=None, extra=None):
        if values is None:
            values = {}
        if extra is None:
            extra = os.getenv('EASY_CONF_EXTRA', 'warn')
        if not extra in ('warn', 'raise', 'ignore'):
            raise ValueError('`extra` argument must be in (warn, raise, ignore)')
        for k, v in self.__class__.get_params().items():
            if isinstance(v, Param):
                v = v.copy()
                if k in values:
                    v.set_value(values.pop(k))
                super().__setitem__(k, v)
            else:
                if k in values and not isinstance(values[k], dict):
                    raise ValueError(
                        'Subconfig for key "{}" must be a dict. '.format(k) +
                        'Received "{}"'.format(type(values[k]))
                    )
                super().__setitem__(k, v(values.pop(k, {})))
        # If there is something left. 
        if values:
            if extra == 'warn':
                warnings.warn(
                    'Received unexpected config values: "%s"\n' %  str(values) +
                    'To disable this warning, set `extra=ignore` or environ '
                    'EASY_CONF_EXTRA=ignore when instantiating the config class.'
                )
            elif extra == 'raise':
                raise ValueError('Received unexpected config values: %s' % str(values))


    def __getitem__(self, key):
        if not key in self:
            raise KeyError('Config does not have key "%s"' % key)
        val = super().__getitem__(key)
        return val.get_value() if isinstance(val, Param) else val

    def __setitem__(self, key, value):
        if not key in self:
            raise KeyError('"%s" is not a valid config key' % key)
        old = super().__getitem__(key)
        if isinstance(old, Param):
            old.set_value(value)
        else:
            super().__setitem__(key, value)

    def __getattribute__(self, key):
        if key.startswith('_') or not key in self:
            return super().__getattribute__(key)
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(str(e))


    def __setattr__(self, key, value):
        if key.startswith('_') or not key in self:
            return super().__setattribute__(key, value)
        else:
            self[key] = value

    @classmethod
    def get_params(cls, ignore_underscore=True):
        params = collections.OrderedDict()
        types = typing.get_type_hints(cls)
        for k, v in get_ordered_members(cls):
            # Ignore everything that starts with underscore
            if ignore_underscore and k.startswith('_'):
                continue
            elif inspect.isclass(v) and issubclass(v, Config):
                params[k] = v #v.get_params(k+'.')
            elif isinstance(v, Param):
                params[k] = v.copy()
            elif k in types:
                params[k] = Param(key=k, type=types[k], default=v)
            elif v is None:
                params[k] = Param(key=k, type=any, default=None)
            elif isinstance(v, (str, bool, float, int, list, tuple, dict)):
                params[k] = Param(key=k, type=type(v), default=v)
        return params

    @classmethod
    def get_parser(cls, hyphenate=False, lowercase=False):
        parser = argparse.ArgumentParser()
        parser.add_argument('_yaml_files', nargs='*', default=[])
        for name, args in cls.get_parser_args(
            hyphenate=hyphenate,
            lowercase=lowercase
        ):
            parser.add_argument('--' + name, **args)
        return parser

    @classmethod
    def get_parser_args(cls, hyphenate=False, lowercase=False, prefix=''):
        for k, v in cls.get_params().items():
            if isinstance(v, Param):
                yield v.get_cli_argument(
                    hyphenate=hyphenate,
                    lowercase=lowercase,
                    prefix=prefix
                )
            else:
                yield from v.get_parser_args(
                    hyphenate=hyphenate,
                    lowercase=lowercase,
                    prefix=prefix + k + '.'
                )

    @classmethod
    def from_cli(cls, hyphenate=False, lowercase=False, **kwargs):
        parser = cls.get_parser(hyphenate=hyphenate, lowercase=lowercase)
        args = vars(parser.parse_args())
        yaml_files = args.pop('_yaml_files') # TODO: USE
        config = {}
        for yaml_file in (yaml_files or []):
            config.update(load_yaml_dict(yaml_file, file=True))
        for k, v in args.items():
            if v is UNSET:
                continue
            parts = k.split('.')
            conf = config
            while len(parts) > 1:
                if not parts[0] in config:
                    conf[parts[0]] = {}
                conf = conf[parts.pop(0)]
            conf[parts[0]] = v
        return cls(config, **kwargs)

    @classmethod
    def from_yaml(cls, file, **kwargs):
        return cls(load_yaml_dict(file, file=True), **kwargs)

    @classmethod
    def from_yaml_string(cls, yaml_string):
        return cls(load_yaml_dict(file, file=False), **kwargs)

    def to_dict(self):
        d = {}
        for k, v in self.items():
            if isinstance(v, Param):
                d[k] = v.get_serialized()
            else:
                d[k] = v.to_dict()
        return d

    def to_yaml(self, file=None):
        yaml_str = yaml.dump(self.to_dict())
        if not file is None:
            if hasattr(file, 'write'):
                file.write(yaml_str)
            else:
                with open(file, 'w') as f:
                    f.write(yaml_str)
        return yaml.dump(self.to_dict())

    def __repr__(self):
        return '{}(...)'.format(self.__class__.__name__)

    def __str__(self):
        yaml_str = self.to_yaml()
        yaml_str = '\n  '.join(s for s in yaml_str.split('\n') if s)
        return '{}(\n  {}\n)'.format(self.__class__.__name__, yaml_str)


def get_ordered_members(cls):
    # TODO: find a clean way to do this
    seen = set()
    members = []
    for c in cls.__mro__:
        if c is Config:
            break
        for k, v in list(vars(c).items())[::-1]:
            if not k.startswith('_') and not k in seen:
                members.append((k, v))
            seen.add(k)
    members = members[::-1]
    return members


def load_yaml_dict(yml, file=False):
    if file:
        if hasattr(yml, 'read'):
            data = yaml.safe_load(yml)
        else:
            with open(yml, 'r') as f:
                data = yaml.safe_load(f)
    else:
        data = yml.safe_load(yml)
    if not isinstance(data, dict):
        raise ValueError('Provided yaml (%s) is not a dict' % yml)
    return data