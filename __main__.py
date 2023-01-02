# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from namespaces import namespaces
from pv import persistentvolumes
import storageclass
import csr
import metrics

nss = namespaces.Namespaces()
kubesystem_ns = nss.get_ns("kube-system")
storageclass.init()
csr.auto_csr_approver(kubesystem_ns.name)
metrics.init_metrics_server(kubesystem_ns.name)


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

vault = k8s.helm.v3.Release(
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
                "standalone": {
                    "enabled": True,
                },
                "dataStorage": {
                    "enabled": True,
                    "size": "500M",
                },
                "auditStorage": {
                    "enabled": True,
                    "size": "500M",
                },
            },
        },
    ),
)


persistentvolumes.PersistentVolume("vault-pv-datastorage", vault_ns.name, "500M")
persistentvolumes.PersistentVolume("vault-pv-auditstorage", vault_ns.name, "500M")
