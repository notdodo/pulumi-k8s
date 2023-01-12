# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi
from namespaces import namespaces
from cni import cilium
import csr
import metrics
import storageclass

nss = namespaces.Namespaces()
nss.create_namespaces(["openebs", "vault", "cilium-system", "osm"])
csr.auto_csr_approver(nss.get_ns("kube-system").name)
metrics.init_metrics_server(nss.get_ns("kube-system").name)
storageclass.init(nss.get_ns("openebs").name, "openebs")
cilium.init_cilium(nss.get_ns("cilium-system").name)

vault = k8s.helm.v3.Release(
    "vault",
    k8s.helm.v3.ReleaseArgs(
        chart="vault",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.releases.hashicorp.com/",
        ),
        namespace=nss.get_ns("vault").name,
        # https://github.com/hashicorp/vault-helm/blob/main/values.yaml
        values={
            "server": {
                "dataStorage": {
                    "enabled": True,
                    "size": "500M",
                },
                "auditStorage": {
                    "enabled": True,
                    "size": "500M",
                },
            },
        },
    ),
)


out = local.Command(
    "unseal-vault",
    create="./vault-utils/unseal.sh",
    opts=pulumi.ResourceOptions(parent=vault, depends_on=vault),
)

k8s.core.v1.Secret(
    "vault-root-token",  # To avoid losing access: TODO remove in prod
    metadata=k8s.meta.v1.ObjectMetaArgs(namespace=nss.get_ns("vault").name),
    immutable=True,
    string_data={"root-token": out.stdout},
)

pulumi.export("vault_root_token", out.stdout)


osm = k8s.helm.v3.Release(
    "osm",
    k8s.helm.v3.ReleaseArgs(
        chart="osm",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://openservicemesh.github.io/osm",
        ),
        namespace=nss.get_ns("osm").name,
        values={
            "osm": {
                "trustDomain": "dodo.local",
                # "certificateProvider": {"kind": "vault"},
            },
        },
    ),
)

# calibre = k8s.helm.v3.Release(
#     "calibre-web",
#     k8s.helm.v3.ReleaseArgs(
#         chart="calibre-web",
#         repository_opts=k8s.helm.v3.RepositoryOptsArgs(
#             repo="https://aste88.github.io/helm-charts/",
#         ),
#         namespace=nss.get_ns("calibre").name,
#         values={
#             "ingress": {"main": {"enabled": True}},
#             "persistence": {
#                 "data": {
#                     "enabled": True,
#                     "mountPath": "/data",
#                 }
#             },
#         },
#     ),
# )
