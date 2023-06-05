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
            version="4.7.0",
            namespace=namespace,
            cleanup_on_fail=True,
            values={
                "controller": {
                    # "hostPort": {"enabled": True},
                    # "service": {
                    #     "type": "NodePort",
                    # },
                    "podAnnotations": {
                        "linkerd.io/inject": "enabled",
                    },
                },
                "rbac": {"create": True},
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
            },
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )

def init_load_balancer(namespace: str, deps: list = []) -> pulumi.Resource:
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
                    "logLevel": "all",
                },
                "speaker": {
                    "logLevel": "all",
                }
            }
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )
    return lb