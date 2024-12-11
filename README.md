# charm-nova-workarounds

This subordinate charm manages Nova workarounds configuration in nova.conf [workarounds] section

## Usage

Deploy this charm as a subordinate to nova-compute:

```bash
charmcraft pack
juju deploy ./nova-workarounds_ubuntu-22.04-amd64.charm
juju add-relation nova-workarounds nova-compute
```

## Configuration

Specify settings in key = value format:
```bash
juju config nova-workarounds skip_cpu_compare_at_startup=true
juju config nova-workarounds skip_cpu_compare_on_dest=true
```

## License

Copyright 2024 The Internet Business Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
