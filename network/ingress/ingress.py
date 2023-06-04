import pulumi
import pulumi_kubernetes as k8s


def init_nginx(namespace: str, deps: list = []):
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
                    "hostPort": {"enabled": True},
                    "service": {
                        "type": "NodePort",
                    },
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
