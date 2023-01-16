import pulumi_kubernetes as k8s


def init_sm(namespace: str):
    k8s.helm.v3.Release(
        "osm",
        k8s.helm.v3.ReleaseArgs(
            chart="osm",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://openservicemesh.github.io/osm",
            ),
            namespace=namespace,
            values={
                "osm": {
                    "trustDomain": "dodo.local",
                    "enablePermissiveTrafficPolicy": True,
                    "deployPrometheus": True,
                    "deployGrafana": True,
                    "deployJaeger": True,
                    "tracing": {"enable": True},
                },
            },
        ),
    )
