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
            version="1.16.1",
            namespace=namespace,
            wait_for_jobs=True,
            cleanup_on_fail=True,
            values={
                "ipam": {"mode": "kubernetes"},
                "image": {"pullPolicy": "IfNotPresent"},
                "k8sServiceHost": "172.18.0.2",
                "k8sServicePort": "6443",
                "kubeProxyReplacement": True,
                # "rollOutCiliumPods": True,
                "operator": {"replicas": 1},
                "kubeProxyReplacement": True,
                # "containerRuntime": {"integration": "crio"},
            },
        ),
        opts=ResourceOptions(depends_on=deps),
    )
    return cilium
