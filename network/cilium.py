import pulumi_kubernetes as k8s
from pulumi import ResourceOptions


def init_cilium(namespace: str = "kube-system", deps: list = []):
    cilium = k8s.helm.v3.Release(
        "cilium",
        k8s.helm.v3.ReleaseArgs(
            chart="cilium",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.cilium.io/",
            ),
            version="1.14.1",
            namespace=namespace,
            wait_for_jobs=True,
            # Only CNI
            values={
                # "debug": {"enabled": True},
                "rollOutCiliumPods": True,
                "operator": {"replicas": 1},
                "containerRuntime": {"integration": "crio"},
                # "bpf": {"tproxy": True},
                # "ingressController": {
                #     "enabled": True,
                #     "loadBalancerMode": "dedicated",
                # },
                # "hubble": {  # Not working
                #     "relay": {
                #         "enabled": True,
                #     },
                #     "ui": {
                #         "enabled": True,
                #     },
                # },
            },
        ),
        opts=ResourceOptions(depends_on=deps),
    )
    return cilium
