import pulumi  # pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s

namespace = k8s.core.v1.Namespace("cilium-system")

cilium = k8s.helm.v3.Release(
    "cilium",
    k8s.helm.v3.ReleaseArgs(
        chart="cilium",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.cilium.io/",
        ),
        namespace=namespace.metadata["name"],
        values={
            "debug": {"enabled": True},
            "operator": {"replicas": 1},
            "containerRuntime": {
                "integration": "crio",
            },
            # "encryption": {"enabled": True, "type": "wireguard"},
            "bpf": {"tproxy": True},
        },
    ),
)
