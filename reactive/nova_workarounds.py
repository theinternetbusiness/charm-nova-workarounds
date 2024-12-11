# Copyright 2024 Your Company Name
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from charmhelpers.core import hookenv
from charmhelpers.core.host import service_restart
from charms.reactive import when, when_not, set_flag, clear_flag, hook
import configparser
import os

@when_not('nova-workarounds.configured')
def configure_nova_workarounds():
    """Configure Nova workarounds."""
    config = hookenv.config()
    nova_conf_path = '/etc/nova/nova.conf'

    try:
        if not os.path.exists(nova_conf_path):
            hookenv.log(f"Nova config {nova_conf_path} does not exist", "ERROR")
            hookenv.status_set('blocked', f'Nova config not found: {nova_conf_path}')
            return

        # Read file contents
        with open(nova_conf_path, 'r') as f:
            content = f.readlines()

        # Find workarounds section or position to insert it
        workarounds_start = -1
        workarounds_end = -1
        next_section_start = -1
        blank_lines_after = 0

        for i, line in enumerate(content):
            if line.strip() == '[workarounds]':
                workarounds_start = i
            elif workarounds_start != -1 and line.startswith('['):
                workarounds_end = i
                next_section_start = i
                # Count blank lines between sections
                for j in range(workarounds_end - 1, workarounds_start, -1):
                    if content[j].strip() == '':
                        blank_lines_after += 1
                    else:
                        break
                break

        # Get config values directly from config
        skip_startup = config['skip_cpu_compare_at_startup']
        skip_dest = config['skip_cpu_compare_on_dest']

        hookenv.log(f"Config values - startup: {skip_startup}, dest: {skip_dest}", "INFO")

        # Convert to string 'true' or 'false' for nova.conf
        startup_value = str(skip_startup).lower()
        dest_value = str(skip_dest).lower()

        # Prepare our workaround settings
        our_settings = [
            f"skip_cpu_compare_at_startup = {startup_value}",
            f"skip_cpu_compare_on_dest = {dest_value}"
        ]

        # If workarounds section exists, update it
        if workarounds_start != -1:
            if workarounds_end == -1:
                workarounds_end = len(content)

            # Get existing settings we want to preserve
            preserved_settings = []
            for line in content[workarounds_start + 1:workarounds_end - blank_lines_after]:
                if '=' in line and not any(setting.split('=')[0].strip() in line for setting in our_settings):
                    preserved_settings.append(line.strip())

            # Combine preserved and our settings
            new_content = (
                content[:workarounds_start + 1] +  # Up to [workarounds]
                [f"{setting}\n" for setting in preserved_settings] +  # Preserved settings
                [f"{setting}\n" for setting in our_settings]  # Our settings
            )

            # Add appropriate number of blank lines before next section
            if blank_lines_after > 0:
                new_content.extend(['\n'] * blank_lines_after)

            # Add the rest of the file
            if next_section_start != -1:
                new_content.extend(content[next_section_start:])
            else:
                new_content.extend(content[workarounds_end:])
        else:
            # Add workarounds section at the end with appropriate spacing
            if content and not content[-1].strip() == '':
                new_content = content + ['\n']
            else:
                new_content = content
            new_content.extend(['[workarounds]\n'] +
                             [f"{setting}\n" for setting in our_settings] +
                             ['\n'])

        # Write back the modified content
        with open(nova_conf_path, 'w') as f:
            f.writelines(new_content)

        # Restart nova-compute service
        service_restart('nova-compute')

        # Set flag and status to indicate configuration is complete
        set_flag('nova-workarounds.configured')
        hookenv.status_set('active', 'Unit is ready')

        hookenv.log(f"Updated nova.conf with skip_cpu_compare_at_startup = {startup_value}", "INFO")
        hookenv.log(f"Updated nova.conf with skip_cpu_compare_on_dest = {dest_value}", "INFO")

    except Exception as e:
        hookenv.log(f'Error configuring Nova workarounds: {e}', level=hookenv.ERROR)
        clear_flag('nova-workarounds.configured')
        hookenv.status_set('blocked', f'Failed to configure: {str(e)}')

@when_not('nova-workarounds.installed')
def install_nova_workarounds():
    """Handle initial installation."""
    hookenv.status_set('maintenance', 'Installing nova-workarounds')
    set_flag('nova-workarounds.installed')
    hookenv.status_set('active', 'Unit is ready')

@hook('config-changed')
def config_changed():
    """Handle configuration changes."""
    hookenv.log("Config changed hook running", "INFO")
    hookenv.status_set('maintenance', 'Updating configuration')
    clear_flag('nova-workarounds.configured')
    configure_nova_workarounds()
