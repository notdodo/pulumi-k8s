from typing import Any, Optional, Union

import pulumi_kubernetes as k8s
from pulumi import Output, Resource, ResourceOptions


def init_cilium(
    namespace: Union[str, Output[Any]] = "kube-system",
    deps: Optional[list[Resource]] = None,
) -> k8s.helm.v3.Release:
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
                "k8sServiceHost": "dev-control-plane",
                "k8sServicePort": "6443",
                "kubeProxyReplacement": True,
                "rollOutCiliumPods": True,
                "operator": {"replicas": 1},
                "containerRuntime": {"integration": "crio"},
            },
        ),
        opts=ResourceOptions(depends_on=deps),
    )
    return cilium
