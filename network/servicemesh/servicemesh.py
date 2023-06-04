import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes_cert_manager import CertManager, ReleaseArgs


def cert_manager(namespace: str, deps: list = []):
    cert_manager = CertManager(
        "cert-manager",
        install_crds=True,
        helm_options=ReleaseArgs(
            namespace=namespace,
            wait_for_jobs=True,
        ),
    )

    trust_manager = k8s.helm.v3.Release(
        "trust-manager",
        k8s.helm.v3.ReleaseArgs(
            chart="trust-manager",
            cleanup_on_fail=True,
            wait_for_jobs=True,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://charts.jetstack.io",
            ),
            version="0.5.0",
            namespace=namespace,
            values={
                "app": {
                    "trust": {"namespace": namespace},
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            parent=cert_manager, depends_on=deps.append(cert_manager)
        ),
    )

    return trust_manager


def init_linkerd(namespace: str, deps: list = []):
    crds = k8s.helm.v3.Release(
        "linkerd-crds",
        k8s.helm.v3.ReleaseArgs(
            chart="linkerd-crds",
            cleanup_on_fail=True,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace,
            wait_for_jobs=True,
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )

    cp = k8s.helm.v3.Release(
        "linkerd-control-plane",
        k8s.helm.v3.ReleaseArgs(
            chart="linkerd-control-plane",
            cleanup_on_fail=True,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace,
            values={
                "identity": {
                    "externalCA": True,
                    "issuer": {"scheme": "kubernetes.io/tls"},
                },
            },
        ),
        opts=pulumi.ResourceOptions(parent=crds, depends_on=deps.append(crds)),
    )

    bootstrapca = k8s.yaml.ConfigFile(
        "bootstrapca",
        "./network/servicemesh/linkerd_bootstrapca.yaml",
        opts=pulumi.ResourceOptions(parent=crds, depends_on=deps.append(crds)),
    )

    k8s.helm.v3.Release(
        "linkerd-viz",
        k8s.helm.v3.ReleaseArgs(
            chart="linkerd-viz",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.linkerd.io/stable",
            ),
            namespace=namespace,
        ),
        opts=pulumi.ResourceOptions(
            parent=cp, depends_on=deps.append([cp, crds, bootstrapca])
        ),
    )

    return cp
