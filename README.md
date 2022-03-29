# easy-conf

Yet another yaml-based config lib for ML and other stuff.

It's not particularly superior to any other config lib, but I have creative control over it.


## Installation 

The package can be found on pypi.

`pip install sherilan-easy-conf`

Or just copy [config.py](./easy_conf/config.py) into your project.

## Usage

Below follows a few examples of how the library can be used.

### Basic 

```python
# example.py
import easy_conf as ec 

# Declare config 
class Config(ec.Config):
  
  foo = 3  # Simply declare a variable like this 
  bar : float = 2.3  # Use type hints to force a data type 
  baz : float = ec.REQUIRED # Forces parser to require this argument 
  
  # You can nest config too 
  class mlp(ec.Config):
    hidden_dim = 64
    hidden_num = 2
  
# Parse it from CLI 
cfg = SubConfig.from_cli()

# Access with dict notation 
print('Foo:', cfg['foo'])

# Or dot notation (just make sure you don't have vars with dict props like `.items`)
print('Bar:', cfg.bar)
print('Baz:', cfg.baz)

# The entire config will be printed as yaml 
print('All config:', cfg)
```

The command line parser is automatically generated. You can access fields of nested config objects with `.`.
```bash
python example.py --baz 3 --mlp.hidden_dim 128
Foo: 3
Bar: 2.3
Baz: 3.0
All config: Config(
  bar: 2.3
  baz: 3.0
  foo: 3
  mlp:
    hidden_dim: 128
    hidden_num: 2
)
```

### Yaml files 

Custom config values can also be read from yaml. 

```yaml
config1.yml

foo: 5
bar: 10
baz: 500
```

```yaml
config2.yml

bar: 11
baz: 99
```

The yaml files can then be specified as positional arguments in the generated argument parser. Yaml config files will be applied one after the other, meaning that conflicting values will use the one provided in the last file (right now it will override at the top level, unfortunately). CLI arguments will also always take presedent over config files.

```bash
python example.py config1.yml config2.yml --baz -1
Foo: 5
Bar: 11.0
Baz: -1.0
All config: Config(
  bar: 11.0
  baz: -1.0
  foo: 5
  mlp:
    hidden_dim: 64
    hidden_num: 2
)
```


### Composition

A master config can be compiled from distinct config classes. 

```python
# Somewhere else 
class MLPConfig(ec.Config):
    hidden_dim = 64
    hidden_num = 2

# Declare config 
class Config(ec.Config):
  
  foo = 3  # Simply declare a variable like this 
  bar : float = 2.3  # Use type hints to force a data type 
  baz : float = ec.REQUIRED # Forces parser to require this argument 
  mlp = MLPConfig 
```

This should give the exact same behavior as previously. 

### Inheritance 

Inheritance should also be supported.

```python
...

class SubConfig(Config):

  foo = 2000  # Override 
  ham = 3  # New value 
  
cfg = SubConfig.from_cli()

...
```
Which gives:
```
python example.py --baz 3 --mlp.hidden_dim 128
Foo: 2000
Bar: 2.3
Baz: 3.0
All config: SubConfig(
  bar: 2.3
  baz: 3.0
  foo: 2000
  ham: 3
  mlp:
    hidden_dim: 128
    hidden_num: 2
)
```

### The Config is a dict 

The Config class is a dicitonary (inherits from OrderedDict) and can be used in most dict-ways, including the `**` operator. For instance.

```python
...

def create_mlp(hidden_dim, hidden_num):
  # Create mlp with hidden_dim and hidden_num as params 
  pass 
  
mlp = create_mlp(**cfg.mlp)
```




