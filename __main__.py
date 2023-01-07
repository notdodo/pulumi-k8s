# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi
from namespaces import namespaces
from pvs import persistentvolumes
from cni import cilium
import csr
import metrics
import storageclass

nss = namespaces.Namespaces()
kubesystem_ns = nss.get_ns("kube-system")
csr.auto_csr_approver(kubesystem_ns.name)
metrics.init_metrics_server(kubesystem_ns.name)
openebs_ns = nss.create_ns("openebs")
storageclass.init(openebs_ns.name, "openebs")

cilium_ns = nss.create_ns("cilium-system")
cilium_dpl = cilium.init_cilium(cilium_ns.name)

vault_ns = nss.create_ns("vault")

vault = k8s.helm.v3.Release(
    "vault",
    k8s.helm.v3.ReleaseArgs(
        chart="vault",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.releases.hashicorp.com/",
        ),
        namespace=vault_ns.name,
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
    "vault-root-token",  # To avoid losing access: TODO
    metadata=k8s.meta.v1.ObjectMetaArgs(namespace=vault_ns.name),
    immutable=True,
    string_data={"root-token": out.stdout},
)

pulumi.export("vault_root_token", out.stdout)
