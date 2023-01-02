import pulumi_kubernetes as k8s


def init_metrics_server(namespace: str):
    metrics_server = k8s.helm.v3.Release(
        "metrics-server",
        k8s.helm.v3.ReleaseArgs(
            chart="metrics-server",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes-sigs.github.io/metrics-server/",
            ),
            namespace=namespace,
        ),
    )
    return metrics_server
