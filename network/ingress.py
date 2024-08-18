from typing import Any, Optional, Union

import pulumi
import pulumi_kubernetes as k8s

config = pulumi.Config()


def init_nginx(
    namespace: Union[str, pulumi.Output[Any]],
    deps: Optional[list[pulumi.Resource]] = None,
) -> k8s.helm.v3.Release:
    return k8s.helm.v3.Release(
        "nginx",
        k8s.helm.v3.ReleaseArgs(
            chart="ingress-nginx",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes.github.io/ingress-nginx",
            ),
            version="4.11.1",
            namespace=namespace,
            cleanup_on_fail=True,
            wait_for_jobs=True,
            values={
                "controller": {
                    "hostPort": {"enabled": True},
                    "kind": "DaemonSet",
                    "podAnnotations": {
                        "linkerd.io/inject": "enabled",
                    },
                    "config": {
                        "use-forwarded-headers": True,
                        "log-format-escape-json": True,
                        "log-format-upstream": " ".join(
                            line.strip()
                            for line in config.get("nginx_log_format", "").splitlines()
                        ),
                        "enable-modsecurity": True,
                        "enable-owasp-modsecurity-crs": True,
                        "modsecurity-snippet": config.get("modsecurity_snippet"),
                    },
                    "service": {"externalIPs": config.get_object("cluster_ips")},
                },
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
            },
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )


def init_load_balancer(
    namespace: Union[str, pulumi.Output[Any]],
    ips: Optional[list[str]] = None,
    deps: Optional[list[pulumi.Resource]] = None,
) -> k8s.helm.v3.Release:
    lb = k8s.helm.v3.Release(
        "metallb",
        k8s.helm.v3.ReleaseArgs(
            chart="metallb",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://metallb.github.io/metallb",
            ),
            version="0.14.8",
            namespace=namespace,
            cleanup_on_fail=True,
            wait_for_jobs=True,
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

    if not deps:
        deps = [lb]
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
        opts=pulumi.ResourceOptions(parent=lb, depends_on=deps),
    )

    deps.append(ipaddr)
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
        opts=pulumi.ResourceOptions(parent=lb, depends_on=deps),
    )
    return lb
