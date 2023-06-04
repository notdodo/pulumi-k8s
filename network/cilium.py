import pulumi_kubernetes as k8s


def init_cilium(namespace: str = "kube-system"):
    cilium = k8s.helm.v3.Release(
        "cilium",
        k8s.helm.v3.ReleaseArgs(
            chart="cilium",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.cilium.io/",
            ),
            version="1.13.3",
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
    )
    return cilium
