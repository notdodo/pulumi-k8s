import json

import pulumi
import pulumi_kubernetes as k8s


def init_nginx(namespace: str, deps: list = []) -> pulumi.Resource:
    return k8s.helm.v3.Release(
        "nginx",
        k8s.helm.v3.ReleaseArgs(
            chart="ingress-nginx",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes.github.io/ingress-nginx",
            ),
            version="4.7.1",
            namespace=namespace,
            cleanup_on_fail=True,
            values={
                "controller": {
                    "hostPort": {"enabled": True},
                    "kind": "DaemonSet",
                    "podAnnotations": {
                        "linkerd.io/inject": "enabled",
                    },
                    "config": {
                        "use-forwarded-headers": True,
                    },
                },
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
            },
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )


def init_load_balancer(
    namespace: str, ips: list = [], deps: list = []
) -> pulumi.Resource:
    lb = k8s.helm.v3.Release(
        "metallb",
        k8s.helm.v3.ReleaseArgs(
            chart="metallb",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://metallb.github.io/metallb",
            ),
            version="0.13.10",
            namespace=namespace,
            cleanup_on_fail=True,
            values={
                "controller": {
                    "logLevel": "warn",
                },
                "speaker": {
                    "logLevel": "warn",
                    "frr": {"enabled": False},
                },
            },
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )

    ipaddr = k8s.apiextensions.CustomResource(
        "IPAddressPool-crd",
        api_version="metallb.io/v1beta1",
        kind="IPAddressPool",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            namespace=namespace,
            name="default",
        ),
        spec={
            "addresses": ips,
        },
        opts=pulumi.ResourceOptions(parent=lb, depends_on=deps.append(lb)),
    )

    k8s.apiextensions.CustomResource(
        "L2Advertisement-crd",
        api_version="metallb.io/v1beta1",
        kind="L2Advertisement",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            namespace=namespace,
            name="default",
        ),
        spec={
            "ipAddressPools": [
                "default",
            ]
        },
        opts=pulumi.ResourceOptions(parent=lb, depends_on=deps.append(ipaddr)),
    )
    return lb
