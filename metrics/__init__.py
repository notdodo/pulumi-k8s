import pulumi
import pulumi_kubernetes as k8s


def init_metrics_server(namespace: str, deps: list = []):
    metrics_server = k8s.helm.v3.Release(
        "metrics-server",
        k8s.helm.v3.ReleaseArgs(
            chart="metrics-server",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://kubernetes-sigs.github.io/metrics-server/",
            ),
            version="3.11.0",
            namespace=namespace,
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )
    return metrics_server


def init_kube_state_metrics(namespace: str, deps: list = []):
    state_metrics = k8s.helm.v3.Release(
        "kube-state-metrics",
        k8s.helm.v3.ReleaseArgs(
            chart="kube-state-metrics",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://prometheus-community.github.io/helm-charts",
            ),
            version="5.14.0",
            namespace=namespace,
            cleanup_on_fail=True,
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )
    return state_metrics
