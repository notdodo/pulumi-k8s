# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from namespaces import namespaces
import storageclass

storageclass.init()

nss = namespaces.Namespaces()

kubesystem_ns = nss.get_ns("kube-system")

auto_csr_approved = k8s.helm.v3.Release(
    "kubelet-csr-approver",
    k8s.helm.v3.ReleaseArgs(
        chart="kubelet-csr-approver",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://postfinance.github.io/kubelet-csr-approver/",
        ),
        namespace=kubesystem_ns.name,
        values={
            "providerRegex": ".*",
            "allowedDNSNames": 10,
            "bypassDnsResolution": True,
            "bypassHostnameCheck": True,
            "providerIpPrefixes": "0.0.0.0/0,::/0",
            "loggingLevel": 10,
        },
    ),
)


metrics_server = k8s.helm.v3.Release(
    "metrics-server",
    k8s.helm.v3.ReleaseArgs(
        chart="metrics-server",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/metrics-server/",
        ),
        namespace=kubesystem_ns.name,
    ),
)

cilium_ns = nss.create_ns("cilium-system")

cilium = k8s.helm.v3.Release(
    "cilium",
    k8s.helm.v3.ReleaseArgs(
        chart="cilium",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.cilium.io/",
        ),
        namespace=cilium_ns.name,
        values={
            "debug": {"enabled": True},
            "operator": {"replicas": 1},
            "containerRuntime": {"integration": "crio"},
            "bpf": {"tproxy": True},
        },
    ),
)


vault_ns = nss.create_ns("vault")

cilium = k8s.helm.v3.Release(
    "vault",
    k8s.helm.v3.ReleaseArgs(
        chart="vault",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.releases.hashicorp.com",
        ),
        namespace=vault_ns.name,
        # https://github.com/hashicorp/vault-helm/blob/main/values.yaml
        values={
            "server": {
                "dataStorage": {
                    "enabled": True,
                    "size": "1Gi",
                },
                "auditStorage": {
                    "enabled": False,
                    "size": "1Gi",
                },
                "dev": {"enabled": True},
            },
        },
    ),
)

k8s.core.v1.PersistentVolume(
    "vault-pv",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="vault-pv", namespace=vault_ns.name),
    spec=k8s.core.v1.PersistentVolumeSpecArgs(
        capacity={"storage": "1Gi"},
        access_modes=["ReadWriteOnce"],
        persistent_volume_reclaim_policy="Retain",
        storage_class_name="default",
        local=k8s.core.v1.LocalVolumeSourceArgs(path="dev/sda2"),
        node_affinity=k8s.core.v1.VolumeNodeAffinityArgs(
            required=k8s.core.v1.NodeSelectorArgs(
                node_selector_terms=[
                    k8s.core.v1.NodeSelectorTermArgs(
                        match_expressions=[
                            k8s.core.v1.NodeSelectorRequirementArgs(
                                key="kubernetes.io/hostname",
                                operator="In",
                                values=["k8sfreenode"],
                            )
                        ]
                    )
                ]
            )
        ),
    ),
)
