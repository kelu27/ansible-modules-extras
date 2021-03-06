#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    search_by_name,
)


ANSIBLE_METADATA = {'status': 'preview',
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ovirt_clusters
short_description: Module to manage clusters in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage clusters in oVirt"
options:
    name:
        description:
            - "Name of the the cluster to manage."
        required: true
    state:
        description:
            - "Should the cluster be present or absent"
        choices: ['present', 'absent']
        default: present
    datacenter:
        description:
            - "Datacenter name where cluster reside."
    description:
        description:
            - "Description of the cluster."
    comment:
        description:
            - "Comment of the cluster."
    network:
        description:
            - "Management network of cluster to access cluster hosts."
    ballooning:
        description:
            - "If (True) enable memory balloon optimization. Memory balloon is used to
               re-distribute / reclaim the host memory based on VM needs
               in a dynamic way."
    virt:
        description:
            - "If (True), hosts in this cluster will be used to run virtual machines."
    gluster:
        description:
            - "If (True), hosts in this cluster will be used as Gluster Storage
               server nodes, and not for running virtual machines."
            - "By default the cluster is created for virtual machine hosts."
    threads_as_cores:
        description:
            - "If (True) the exposed host threads would be treated as cores
               which can be utilized by virtual machines."
    ksm:
        description:
            - "I (True) MoM enables to run Kernel Same-page Merging (KSM) when
               necessary and when it can yield a memory saving benefit that
               outweighs its CPU cost."
    ksm_numa:
        description:
            - "If (True) enables KSM C(ksm) for best berformance inside NUMA nodes."
    ha_reservation:
        description:
            - "If (True) enable the oVirt to monitor cluster capacity for highly
               available virtual machines."
    trusted_service:
        description:
            - "If (True) enable integration with an OpenAttestation server."
    vm_reason:
        description:
            - "If (True) enable an optional reason field when a virtual machine
               is shut down from the Manager, allowing the administrator to
               provide an explanation for the maintenance."
    host_reason:
        description:
            - "If (True) enable an optional reason field when a host is placed
               into maintenance mode from the Manager, allowing the administrator
               to provide an explanation for the maintenance."
    memory_policy:
        description:
            - "I(disabled) - Disables memory page sharing."
            - "I(server) - Sets the memory page sharing threshold to 150% of the system memory on each host."
            - "I(desktop) - Sets the memory page sharing threshold to 200% of the system memory on each host."
        choices: ['disabled', 'server', 'desktop']
    rng_sources:
        description:
            - "List that specify the random number generator devices that all hosts in the cluster will use."
            - "Supported generators are: I(hwrng) and I(random)."
    spice_proxy:
        description:
            - "The proxy by which the SPICE client will connect to virtual machines."
            - "The address must be in the following format: I(protocol://[host]:[port])"
    fence_enabled:
        description:
            - "If (True) enables fencing on the cluster."
            - "Fencing is enabled by default."
    fence_skip_if_sd_active:
        description:
            - "If (True) any hosts in the cluster that are Non Responsive
               and still connected to storage will not be fenced."
    fence_skip_if_connectivity_broken:
        description:
            - "If (True) fencing will be temporarily disabled if the percentage
               of hosts in the cluster that are experiencing connectivity issues
               is greater than or equal to the defined threshold."
            - "The threshold can be specified by C(fence_connectivity_threshold)."
    fence_connectivity_threshold:
        description:
            - "The threshold used by C(fence_skip_if_connectivity_broken)."
    resilience_policy:
        description:
            - "The resilience policy defines how the virtual machines are prioritized in the migration."
            - "Following values are supported:"
            - "C(do_not_migrate) -  Prevents virtual machines from being migrated. "
            - "C(migrate) - Migrates all virtual machines in order of their defined priority."
            - "C(migrate_highly_available) - Migrates only highly available virtual machines to prevent overloading other hosts."
        choices: ['do_not_migrate', 'migrate', 'migrate_highly_available']
    migration_bandwidth:
        description:
            - "The bandwidth settings define the maximum bandwidth of both outgoing and incoming migrations per host."
            - "Following bandwith options are supported:"
            - "C(auto) - Bandwidth is copied from the I(rate limit) [Mbps] setting in the data center host network QoS."
            - "C(hypervisor_default) - Bandwidth is controlled by local VDSM setting on sending host."
            - "C(custom) - Defined by user (in Mbps)."
        choices: ['auto', 'hypervisor_default', 'custom']
    migration_bandwidth_limit:
        description:
            - "Set the I(custom) migration bandwidth limit."
            - "This parameter is used only when C(migration_bandwidth) is I(custom)."
    migration_auto_converge:
        description:
            - "If (True) auto-convergence is used during live migration of virtual machines."
            - "Used only when C(migration_policy) is set to I(legacy)."
            - "Following options are supported:"
            - "C(true) - Override the global setting to I(true)."
            - "C(false) - Override the global setting to I(false)."
            - "C(inherit) - Use value which is set globally."
        choices: ['true', 'false', 'inherit']
    migration_compressed:
        description:
            - "If (True) compression is used during live migration of the virtual machine."
            - "Used only when C(migration_policy) is set to I(legacy)."
            - "Following options are supported:"
            - "C(true) - Override the global setting to I(true)."
            - "C(false) - Override the global setting to I(false)."
            - "C(inherit) - Use value which is set globally."
        choices: ['true', 'false', 'inherit']
    migration_policy:
        description:
            - "A migration policy defines the conditions for live migrating
               virtual machines in the event of host failure."
            - "Following policies are supported:"
            - "C(legacy) - Legacy behavior of 3.6 version."
            - "C(minimal_downtime) - Virtual machines should not experience any significant downtime."
            - "C(suspend_workload) - Virtual machines may experience a more significant downtime."
        choices: ['legacy', 'minimal_downtime', 'suspend_workload']
    serial_policy:
        description:
            - "Specify a serial number policy for the virtual machines in the cluster."
            - "Following options are supported:"
            - "C(vm) - Sets the virtual machine's UUID as its serial number."
            - "C(host) - Sets the host's UUID as the virtual machine's serial number."
            - "C(custom) - Allows you to specify a custom serial number in C(serial_policy_value)."
    serial_policy_value:
        description:
            - "Allows you to specify a custom serial number."
            - "This parameter is used only when C(serial_policy) is I(custom)."
    scheduling_policy:
        description:
            - "Name of the scheduling policy to be used for cluster."
    cpu_arch:
        description:
            - "CPU architecture of cluster."
        choices: ['x86_64', 'ppc64', 'undefined']
    cpu_type:
        description:
            - "CPU codename. For example I(Intel SandyBridge Family)."
    switch_type:
        description:
            - "Type of switch to be used by all networks in given cluster.
               Either I(legacy) which is using linux brigde or I(ovs) using
               Open vSwitch."
        choices: ['legacy', 'ovs']
    compatibility_version:
        description:
            - "The compatibility version of the cluster. All hosts in this
               cluster must support at least this compatibility version."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create cluster
- ovirt_clusters:
    datacenter: mydatacenter
    name: mycluster
    cpu_type: Intel SandyBridge Family
    description: mycluster
    compatibility_version: 4.0

# Create virt service cluster:
- ovirt_clusters:
    datacenter: mydatacenter
    name: mycluster
    cpu_type: Intel Nehalem Family
    description: mycluster
    switch_type: legacy
    compatibility_version: 4.0
    ballooning: true
    gluster: false
    threads_as_cores: true
    ha_reservation: true
    trusted_service: false
    host_reason: false
    vm_reason: true
    ksm_numa: true
    memory_policy: server
    rng_sources:
      - hwrng
      - random

# Remove cluster
- ovirt_clusters:
    state: absent
    name: mycluster
'''

RETURN = '''
id:
    description: ID of the cluster which is managed
    returned: On success if cluster is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
cluster:
    description: "Dictionary of all the cluster attributes. Cluster attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/cluster."
    returned: On success if cluster is found.
'''


class ClustersModule(BaseModule):

    def __get_major(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.major
        return int(full_version.split('.')[0])

    def __get_minor(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.minor
        return int(full_version.split('.')[1])

    def param(self, name, default=None):
        return self._module.params.get(name, default)

    def _get_memory_policy(self):
        memory_policy = self.param('memory_policy')
        if memory_policy == 'desktop':
            return 200
        elif memory_policy == 'server':
            return 150
        elif memory_policy == 'disabled':
            return 100

    def _get_policy_id(self):
        # These are hardcoded IDs, once there is API, please fix this.
        # legacy - 00000000-0000-0000-0000-000000000000
        # minimal downtime - 80554327-0569-496b-bdeb-fcbbf52b827b
        # suspend workload if needed - 80554327-0569-496b-bdeb-fcbbf52b827c
        migration_policy = self.param('migration_policy')
        if migration_policy == 'legacy':
            return '00000000-0000-0000-0000-000000000000'
        elif migration_policy == 'minimal_downtime':
            return '80554327-0569-496b-bdeb-fcbbf52b827b'
        elif migration_policy == 'suspend_workload':
            return '80554327-0569-496b-bdeb-fcbbf52b827c'

    def _get_sched_policy(self):
        sched_policy = None
        if self.param('serial_policy'):
            sched_policies_service = self._connection.system_service().scheduling_policies_service()
            sched_policy = search_by_name(sched_policies_service, self.param('scheduling_policy'))
            if not sched_policy:
                raise Exception("Scheduling policy '%s' was not found" % self.param('scheduling_policy'))

        return sched_policy

    def build_entity(self):
        sched_policy = self._get_sched_policy()
        return otypes.Cluster(
            name=self.param('name'),
            comment=self.param('comment'),
            description=self.param('description'),
            ballooning_enabled=self.param('ballooning'),
            gluster_service=self.param('gluster'),
            virt_service=self.param('virt'),
            threads_as_cores=self.param('threads_as_cores'),
            ha_reservation=self.param('ha_reservation'),
            trusted_service=self.param('trusted_service'),
            optional_reason=self.param('vm_reason'),
            maintenance_reason_required=self.param('host_reason'),
            scheduling_policy=otypes.SchedulingPolicy(
                id=sched_policy.id,
            ) if sched_policy else None,
            serial_number=otypes.SerialNumber(
                policy=otypes.SerialNumberPolicy(self.param('serial_policy')),
                value=self.param('serial_policy_value'),
            ) if (
                self.param('serial_policy') is not None or
                self.param('serial_policy_value') is not None
            ) else None,
            migration=otypes.MigrationOptions(
                auto_converge=otypes.InheritableBoolean(
                    self.param('migration_auto_converge'),
                ) if self.param('migration_auto_converge') else None,
                bandwidth=otypes.MigrationBandwidth(
                    assignment_method=otypes.MigrationBandwidthAssignmentMethod(
                        self.param('migration_bandwidth'),
                    ) if self.param('migration_bandwidth') else None,
                    custom_value=self.param('migration_bandwidth_limit'),
                ) if (
                    self.param('migration_bandwidth') or
                    self.param('migration_bandwidth_limit')
                ) else None,
                compressed=otypes.InheritableBoolean(
                    self.param('migration_compressed'),
                ) if self.param('migration_compressed') else None,
                policy=otypes.MigrationPolicy(
                    id=self._get_policy_id()
                ) if self.param('migration_policy') else None,
            ) if (
                self.param('migration_bandwidth') is not None or
                self.param('migration_bandwidth_limit') is not None or
                self.param('migration_auto_converge') is not None or
                self.param('migration_compressed') is not None or
                self.param('migration_policy') is not None
            ) else None,
            error_handling=otypes.ErrorHandling(
                on_error=otypes.MigrateOnError(
                    self.param('resilience_policy')
                ),
            ) if self.param('resilience_policy') else None,
            fencing_policy=otypes.FencingPolicy(
                enabled=(
                    self.param('fence_enabled') or
                    self.param('fence_skip_if_connectivity_broken') or
                    self.param('fence_skip_if_sd_active')
                ),
                skip_if_connectivity_broken=otypes.SkipIfConnectivityBroken(
                    enabled=self.param('fence_skip_if_connectivity_broken'),
                    threshold=self.param('fence_connectivity_threshold'),
                ) if (
                    self.param('fence_skip_if_connectivity_broken') is not None or
                    self.param('fence_connectivity_threshold') is not None
                ) else None,
                skip_if_sd_active=otypes.SkipIfSdActive(
                    enabled=self.param('fence_skip_if_sd_active'),
                ) if self.param('fence_skip_if_sd_active') else None,
            ) if (
                self.param('fence_enabled') is not None or
                self.param('fence_skip_if_sd_active') is not None or
                self.param('fence_skip_if_connectivity_broken') is not None or
                self.param('fence_connectivity_threshold') is not None
            ) else None,
            display=otypes.Display(
                proxy=self.param('spice_proxy'),
            ) if self.param('spice_proxy') else None,
            required_rng_sources=[
                otypes.RngSource(rng) for rng in self.param('rng_sources')
            ] if self.param('rng_sources') else None,
            memory_policy=otypes.MemoryPolicy(
                over_commit=otypes.MemoryOverCommit(
                    percent=self._get_memory_policy(),
                ),
            ) if self.param('memory_policy') else None,
            ksm=otypes.Ksm(
                enabled=self.param('ksm') or self.param('ksm_numa'),
                merge_across_nodes=not self.param('ksm_numa'),
            ) if (
                self.param('ksm_numa') is not None or
                self.param('ksm') is not None
            ) else None,
            data_center=otypes.DataCenter(
                name=self.param('datacenter'),
            ) if self.param('datacenter') else None,
            management_network=otypes.Network(
                name=self.param('network'),
            ) if self.param('network') else None,
            cpu=otypes.Cpu(
                architecture=self.param('cpu_arch'),
                type=self.param('cpu_type'),
            ) if (
                self.param('cpu_arch') or self.param('cpu_type')
            ) else None,
            version=otypes.Version(
                major=self.__get_major(self.param('compatibility_version')),
                minor=self.__get_minor(self.param('compatibility_version')),
            ) if self.param('compatibility_version') else None,
            switch_type=otypes.SwitchType(
                self.param('switch_type')
            ) if self.param('switch_type') else None,
        )

    def update_check(self, entity):
        return (
            equal(self.param('comment'), entity.comment) and
            equal(self.param('description'), entity.description) and
            equal(self.param('switch_type'), str(entity.switch_type)) and
            equal(self.param('cpu_arch'), str(entity.cpu.architecture)) and
            equal(self.param('cpu_type'), entity.cpu.type) and
            equal(self.param('ballooning'), entity.ballooning_enabled) and
            equal(self.param('gluster'), entity.gluster_service) and
            equal(self.param('virt'), entity.virt_service) and
            equal(self.param('threads_as_cores'), entity.threads_as_cores) and
            equal(self.param('ksm_numa'), not entity.ksm.merge_across_nodes and entity.ksm.enabled) and
            equal(self.param('ksm'), entity.ksm.merge_across_nodes and entity.ksm.enabled) and
            equal(self.param('ha_reservation'), entity.ha_reservation) and
            equal(self.param('trusted_service'), entity.trusted_service) and
            equal(self.param('host_reason'), entity.maintenance_reason_required) and
            equal(self.param('vm_reason'), entity.optional_reason) and
            equal(self.param('spice_proxy'), getattr(entity.display, 'proxy', None)) and
            equal(self.param('fence_enabled'), entity.fencing_policy.enabled) and
            equal(self.param('fence_skip_if_sd_active'), entity.fencing_policy.skip_if_sd_active.enabled) and
            equal(self.param('fence_skip_if_connectivity_broken'), entity.fencing_policy.skip_if_connectivity_broken.enabled) and
            equal(self.param('fence_connectivity_threshold'), entity.fencing_policy.skip_if_connectivity_broken.threshold) and
            equal(self.param('resilience_policy'), str(entity.error_handling.on_error)) and
            equal(self.param('migration_bandwidth'), str(entity.migration.bandwidth.assignment_method)) and
            equal(self.param('migration_auto_converge'), str(entity.migration.auto_converge)) and
            equal(self.param('migration_compressed'), str(entity.migration.compressed)) and
            equal(self.param('serial_policy'), str(entity.serial_number.policy)) and
            equal(self.param('serial_policy_value'), entity.serial_number.value) and
            equal(self.param('scheduling_policy'), self._get_sched_policy().name) and
            equal(self._get_policy_id(), entity.migration.policy.id) and
            equal(self._get_memory_policy(), entity.memory_policy.over_commit.percent) and
            equal(self.__get_minor(self.param('compatibility_version')), self.__get_minor(entity.version)) and
            equal(self.__get_major(self.param('compatibility_version')), self.__get_major(entity.version)) and
            equal(
                self.param('migration_bandwidth_limit') if self.param('migration_bandwidth') == 'custom' else None,
                entity.migration.bandwidth.custom_value
            ) and
            equal(
                sorted(self.param('rng_sources')) if self.param('rng_sources') else None,
                sorted([
                    str(source) for source in entity.required_rng_sources
                ])
            )
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, required=True),
        ballooning=dict(default=None, type='bool', aliases=['balloon']),
        gluster=dict(default=None, type='bool'),
        virt=dict(default=None, type='bool'),
        threads_as_cores=dict(default=None, type='bool'),
        ksm_numa=dict(default=None, type='bool'),
        ksm=dict(default=None, type='bool'),
        ha_reservation=dict(default=None, type='bool'),
        trusted_service=dict(default=None, type='bool'),
        vm_reason=dict(default=None, type='bool'),
        host_reason=dict(default=None, type='bool'),
        memory_policy=dict(default=None, choices=['disabled', 'server', 'desktop']),
        rng_sources=dict(default=None, type='list'),
        spice_proxy=dict(default=None),
        fence_enabled=dict(default=None, type='bool'),
        fence_skip_if_sd_active=dict(default=None, type='bool'),
        fence_skip_if_connectivity_broken=dict(default=None, type='bool'),
        fence_connectivity_threshold=dict(default=None, type='int'),
        resilience_policy=dict(default=None, choices=['migrate_highly_available', 'migrate', 'do_not_migrate']),
        migration_bandwidth=dict(default=None, choices=['auto', 'hypervisor_default', 'custom']),
        migration_bandwidth_limit=dict(default=None, type='int'),
        migration_auto_converge=dict(default=None, choices=['true', 'false', 'inherit']),
        migration_compressed=dict(default=None, choices=['true', 'false', 'inherit']),
        migration_policy=dict(default=None, choices=['legacy', 'minimal_downtime', 'suspend_workload']),
        serial_policy=dict(default=None, choices=['vm', 'host', 'custom']),
        serial_policy_value=dict(default=None),
        scheduling_policy=dict(default=None),
        datacenter=dict(default=None),
        description=dict(default=None),
        comment=dict(default=None),
        network=dict(default=None),
        cpu_arch=dict(default=None, choices=['ppc64', 'undefined', 'x86_64']),
        cpu_type=dict(default=None),
        switch_type=dict(default=None, choices=['legacy', 'ovs']),
        compatibility_version=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        clusters_service = connection.system_service().clusters_service()
        clusters_module = ClustersModule(
            connection=connection,
            module=module,
            service=clusters_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = clusters_module.create()
        elif state == 'absent':
            ret = clusters_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=False)


if __name__ == "__main__":
    main()
