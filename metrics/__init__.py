import pulumi_kubernetes as k8s
import pulumi


def init_metrics_server(namespace: str, deps: list = []):
    metrics_server = k8s.helm.v3.Release(
        "metrics-server",
        k8s.helm.v3.ReleaseArgs(
            chart="metrics-server",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes-sigs.github.io/metrics-server/",
            ),
            namespace=namespace,
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )
    return metrics_server
