# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi
from namespaces import namespaces
from cni import cilium

# from servicemesh import servicemesh as sm
import csr
import metrics
import storageclass

nss = namespaces.Namespaces()
nss.create_namespaces(["openebs", "vault", "cilium-system"])
cilium.init_cilium(nss.get_ns("cilium-system").name)
csr.auto_csr_approver(nss.get_ns("kube-system").name)
storageclass.init(nss.get_ns("openebs").name, "openebs")
metrics.init_metrics_server(nss.get_ns("kube-system").name)
# sm.init_sm(nss.get_ns("osm").name)

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
    opts=pulumi.ResourceOptions(parent=vault, depends_on=out),
)

pulumi.export("vault_root_token", out.stdout)


nss.create_ns("argocd", fixed_name=True)
nss.create_ns("juicer", fixed_name=True)


def set_namespace(obj, opts):
    if "namespace" not in obj["metadata"]:
        obj["metadata"]["namespace"] = nss.get_ns("argocd").name


argocd = k8s.yaml.ConfigFile(
    "argocd",
    "./argocd/install.yaml",
    transformations=[set_namespace],
)

argocd = k8s.yaml.ConfigFile(
    "argocd-juicer-app",
    "./argocd/juicer-app.yaml",
)
