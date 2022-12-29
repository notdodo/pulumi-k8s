# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from namespaces import namespaces

nss = namespaces.Namespaces()

metrics_server = k8s.helm.v3.Release(
    "metrics-server",
    k8s.helm.v3.ReleaseArgs(
        chart="metrics-server",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/metrics-server/",
        ),
        namespace="kube-system",
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
            "containerRuntime": {
                "integration": "crio",
            },
            "bpf": {"tproxy": True},
        },
    ),
)
