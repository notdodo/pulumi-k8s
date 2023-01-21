import pulumi_kubernetes as k8s


def init_argocd(namespace: str = "argocd"):
    def set_namespace(obj, opts):
        if "namespace" not in obj["metadata"]:
            obj["metadata"]["namespace"] = namespace

    argocd = k8s.yaml.ConfigFile(
        "argocd",
        "./install.yaml",
        transformations=[set_namespace],
    )

    argocd = k8s.yaml.ConfigFile(
        "argocd-juicer-app",
        "./juicer-app.yaml",
    )
